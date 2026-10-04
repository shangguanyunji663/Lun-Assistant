"""RAG 阶段三：交叉编码器精排（bge-reranker，sentence-transformers 本地加载）。

⚠️ 关键：模型加载与推理是纯同步 CPU 阻塞操作（首载 10~60s，推理 5~30s），
必须在线程池中执行，绝不能直接跑在 asyncio 事件循环线程上，否则会冻结
整个服务（SSE 中断、其他请求全部挂起）。
"""
import asyncio
import logging
import os
import threading
import time
from pathlib import Path

from infrastructure.config import get_value

logger = logging.getLogger("lunjiang.rag")


def _set_offline_if_cached(model_name: str) -> None:
    """本地缓存已存在时强制 HF 离线模式，避免每次加载都探测网络导致分钟级阻塞。"""
    hf_home = os.environ.get("HF_HOME") or str(Path.home() / ".cache" / "huggingface")
    repo_dir = Path(hf_home) / "hub" / f"models--{model_name.replace('/', '--')}" / "snapshots"
    if repo_dir.is_dir() and any(repo_dir.glob("*/config.json")):
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


class Reranker:
    _lock = threading.Lock()
    _model = None
    _load_lock = asyncio.Lock()  # async 侧保护，避免并发重复触发 to_thread 加载

    # ---------- 同步侧（线程池内调用）----------
    @classmethod
    def _sync_get_model(cls):
        with cls._lock:
            if cls._model is None:
                name = get_value("rerank", "model", default="BAAI/bge-reranker-base")
                _set_offline_if_cached(name)
                from sentence_transformers import CrossEncoder
                device = get_value("rerank", "device", default="cpu")
                logger.info("加载交叉编码器 %s (%s)...", name, device)
                t0 = time.monotonic()
                cls._model = CrossEncoder(name, device=device,
                                          max_length=int(get_value("rerank", "max_length", default=512)))
                # 首次推理预热：模型加载完成 ≠ 可服务，首跑还有内核编译开销（数秒）。
                # 不在这里付掉就会转嫁给第一次真实检索（实测冷启动合计可达 90s）。
                cls._model.predict([("预热", "预热文本")])
                logger.info("交叉编码器加载完成（%.1fs，含首次推理预热）",
                            time.monotonic() - t0)
            return cls._model

    @staticmethod
    def _sync_rerank(model, query: str, candidates: list[dict], top_k: int,
                     alt_query: str | None) -> list[dict]:
        scores = model.predict([(query, c["content"]) for c in candidates])
        if alt_query and alt_query != query:
            alt_scores = model.predict([(alt_query, c["content"]) for c in candidates])
            scores = [max(s, sa) for s, sa in zip(scores, alt_scores)]
        for c, s in zip(candidates, scores):
            c["rerank_score"] = float(s)
        ranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
        return ranked[:top_k]

    # ---------- async 侧（对外 API）----------
    @classmethod
    async def preload(cls) -> float | None:
        """后台预加载（含首次推理）：启动期调用，避免首次用户请求时阻塞 10~60s。

        返回加载耗时（秒）；已加载返回 None，失败留痕日志后返回 None（调用方
        由此区分「预热成功」与「静默失败」——后者意味着每次首检都要付冷启动成本）。
        """
        async with cls._load_lock:
            if cls._model is not None:
                return None
            try:
                t0 = time.monotonic()
                await asyncio.to_thread(cls._sync_get_model)
                return time.monotonic() - t0
            except Exception:
                logger.warning("交叉编码器预加载失败，将在首次检索时懒加载", exc_info=True)
                return None

    async def rerank(self, query: str, candidates: list[dict], top_k: int = 5,
                     alt_query: str | None = None) -> list[dict]:
        """交叉编码器精排（线程池执行，不阻塞事件循环）。"""
        if not candidates:
            return []
        async with self._load_lock:
            model = await asyncio.to_thread(self._sync_get_model)
        return await asyncio.to_thread(
            self._sync_rerank, model, query, candidates, top_k, alt_query)


reranker = Reranker()
