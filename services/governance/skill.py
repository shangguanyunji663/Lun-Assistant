"""BehaviorTracker 与 Skill 动态生成。

- observe(): 监听每次工具调用（agent/tool/参数/成败），Redis 累计同模式计数。
- 同模式累计 3 次成功 → 自动沉淀为可复用 Skill（落库 skills 表）。
- match_skills(): 三维匹配排序（意图语义相似度 / 参数模式相似度 / 历史成功率），
  供 Agent 调度时优先复用已验证的操作路径。
"""
import hashlib
import json
import logging
import math
from typing import Any

from sqlalchemy import select

from infrastructure.config import get_value
from infrastructure.db import get_session_factory
from infrastructure.models.skill import Skill
from infrastructure.redis_client import get_redis
from services.llm.provider import LLMProvider

logger = logging.getLogger("lunjiang.skill")

_PATTERN_KEY = "behavior:{agent}:{digest}"


def _pattern_digest(agent: str, tool: str, params: dict[str, Any]) -> str:
    """规范化参数形状：只保留参数名与值类型，屏蔽具体取值波动。"""
    shape = {k: type(v).__name__ for k, v in sorted(params.items())}
    raw = json.dumps({"agent": agent, "tool": tool, "shape": shape},
                     sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


class BehaviorTracker:
    async def observe(self, *, agent: str, tool: str, params: dict, ok: bool,
                      user_id: int | None) -> None:
        digest = _pattern_digest(agent, tool, params)
        threshold = int(get_value("governance", "skill", "pattern_threshold", default=3))
        r = get_redis()
        key = _PATTERN_KEY.format(agent=agent, digest=digest)
        pipe = r.pipeline()
        pipe.hincrby(key, "total", 1)
        if ok:
            pipe.hincrby(key, "ok", 1)
        pipe.hset(key, "last_params", json.dumps(params, ensure_ascii=False, default=str))
        pipe.expire(key, 7 * 24 * 3600)
        await pipe.execute()
        h = await r.hgetall(key)
        total = int(h.get("total", 0))
        ok_cnt = int(h.get("ok", 0))
        last = h.get("last_params", "{}")
        if ok and ok_cnt >= threshold and ok_cnt == total:
            await self._materialize_skill(agent, tool, digest, json.loads(last), user_id)

    async def _materialize_skill(self, agent: str, tool: str, digest: str,
                                 params: dict, user_id: int | None) -> None:
        """同模式连续成功达阈值 → 生成 Skill（幂等：存在即跳过）。"""
        try:
            async with get_session_factory()() as db:
                exists = await db.scalar(
                    select(Skill).where(Skill.agent == agent,
                                        Skill.pattern["digest"].as_string() == digest))
                if exists:
                    return
                skill = Skill(
                    name=f"{agent}.{tool}.auto",
                    agent=agent,
                    pattern={"digest": digest, "tool": tool,
                             "shape": {k: type(v).__name__ for k, v in sorted(params.items())}},
                    params_template=params,
                    description=f"BehaviorTracker 自动沉淀：{agent} 反复成功执行 {tool} 的参数模式",
                    created_by=user_id,
                )
                db.add(skill)
                await db.commit()
                logger.info("[skill] 自动沉淀 Skill: %s (digest=%s)", skill.name, digest)
        except Exception:
            logger.exception("Skill 沉淀失败 agent=%s tool=%s", agent, tool)

    async def record_usage(self, skill_id: int, ok: bool) -> None:
        """Skill 被复用后回写统计，供三维排序使用。"""
        async with get_session_factory()() as db:
            skill = await db.get(Skill, skill_id)
            if skill is None:
                return
            skill.usage_count += 1
            if ok:
                skill.success_count += 1
            skill.score = self._score(skill)
            await db.commit()

    @staticmethod
    def _score(skill: Skill) -> float:
        success_rate = skill.success_count / skill.usage_count if skill.usage_count else 0.5
        # 维度1 成功率(0~1) + 维度2 使用频度对数(0~1) + 维度3 新鲜度由查询时算
        freq = min(1.0, math.log1p(skill.usage_count) / math.log(50))
        return 0.6 * success_rate + 0.4 * freq

    async def match_skills(self, agent: str, query: str, params_hint: dict | None = None,
                           top_k: int = 3) -> list[Skill]:
        """三维匹配排序：意图语义相似度 / 参数模式相似度 / 成功率频度分。"""
        async with get_session_factory()() as db:
            skills = (await db.execute(
                select(Skill).where(Skill.agent == agent).order_by(Skill.score.desc())
            )).scalars().all()
        if not skills:
            return []
        # 维度1：意图语义相似度（embedding 余弦），Skill 少时批量编码成本低
        try:
            provider = LLMProvider()
            texts = [f"{s.description} {s.pattern.get('tool', '')}" for s in skills]
            vecs = await provider.embed([query] + texts)
            q, mat = vecs[0], vecs[1:]
            def cos(a, b):
                na, nb = sum(x * x for x in a) ** 0.5, sum(x * x for x in b) ** 0.5
                return sum(x * y for x, y in zip(a, b)) / (na * nb or 1)
            intent_scores = [cos(q, v) for v in mat]
        except Exception:
            intent_scores = [0.0] * len(skills)
        # 维度2：参数模式相似度（参数名重合率）
        hint_keys = set((params_hint or {}).keys())

        def param_sim(s: Skill) -> float:
            keys = set(s.pattern.get("shape", {}).keys())
            if not keys and not hint_keys:
                return 0.5
            return len(keys & hint_keys) / max(1, len(keys | hint_keys))

        ranked = sorted(
            zip(skills, intent_scores),
            key=lambda pair: 0.5 * pair[1] + 0.3 * param_sim(pair[0]) + 0.2 * pair[0].score,
            reverse=True,
        )
        return [s for s, _ in ranked[:top_k]]


behavior_tracker = BehaviorTracker()
