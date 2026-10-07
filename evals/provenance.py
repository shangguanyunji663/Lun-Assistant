"""评测产物「身份证」：让每个数字都能被第三方复现与对账。

背景（为什么需要这个模块）：
    2026-09-04 数据集从 22/8 条扩到 50/20 条后，评测没重跑，`evals/results_latest.json`
    仍是旧规模产物，而落地页/README 已按新口径宣称 100% —— 数字链条断裂，
    面试官打开产物文件 30 秒就能看出对不上。

    根因不是"数字写错了"，而是**产物里没有任何可追溯信息**：没有时间、没有代码版本、
    没有数据集指纹、没有模型名。读产物的人无法判断它是不是当前代码跑出来的。

    修法：每次评测自动记录 provenance（本文档所称"身份证"），使
    「页面数字 → 产物 → 数据集 + 代码版本 + 模型」四者可以互相验证；
    数字一旦与产物不一致，就是可检测的缺陷，而不是需要互相"相信"的声明。

产物结构（`evals/results_latest.json`）：
    {
      "_provenance": {
        "schema": "evals/provenance@1",
        "generated_at": "2026-10-05T18:12:33+08:00",   # 本地时区 ISO8601
        "git": {"revision": "c622764", "dirty": true,
                 "dirty_files": ["evals/harness.py"], "branch": "main"},
        "host": {"platform": "Windows-10-...", "python": "3.11.x"},
        "models": {"chat": "qwen3:4b-ctx4096", "embedding": "bge-m3",
                   "embedding_dim": 1024, "rerank": "BAAI/bge-reranker-base"},
        "suites": {"intent": {"dataset": "evals/datasets/intent.jsonl",
                              "cases": 50, "sha256": "..."}}
      },
      "intent": {...}, "rag": {...}, "compression": {...}
    }

    `dirty=true` 说明评测跑在未提交的工作区上 —— 这是**诚实标记**，不是错误：
    重跑后重新提交即可让产物从 dirty 变干净。

用法（无需外部服务）：
    from evals.provenance import build_provenance, summarize_provenance

    prov = build_provenance({"intent": "intent.jsonl"})
    print(summarize_provenance(prov))
"""
from __future__ import annotations

import hashlib
import platform
import subprocess
import sys
from datetime import datetime, timezone

from infrastructure.paths import PROJECT_ROOT

SCHEMA = "evals/provenance@1"
DATASET_DIR = PROJECT_ROOT / "evals" / "datasets"

# 复现口径：这些是"换一个值结果就不同"的底座，必须记进产物
_MODEL_KEYS = (
    ("chat", ("llm", "providers", "ollama", "chat_model")),
    ("embedding", ("llm", "providers", "ollama", "embedding_model")),
    ("embedding_dim", ("llm", "providers", "ollama", "embedding_dim")),
    ("rerank", ("rerank", "model")),
)


def _git(*args: str) -> str:
    """执行 git 命令；失败返回空串（无 git 环境时不应让评测崩掉）。"""
    try:
        out = subprocess.run(
            ["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True,
            timeout=10, encoding="utf-8", errors="replace",
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def git_fingerprint() -> dict:
    """代码版本指纹：revision + 是否有未提交改动（脏工作区的评测结果需标注）。"""
    revision = _git("rev-parse", "--short", "HEAD")
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    dirty_files = [line for line in _git("status", "--porcelain").splitlines() if line.strip()]
    return {
        "revision": revision or "(no-git)",
        "branch": branch or "(no-git)",
        "dirty": bool(dirty_files),
        "dirty_files": dirty_files[:20],
    }


def dataset_fingerprint(filename: str) -> dict:
    """数据集指纹：条数 + 内容 sha256。

    条数与 sha256 一起记录的理由：条数能暴露"数据集扩了但没重跑"，
    sha256 能暴露"样本被替换过"（哪怕条数没变）。
    """
    path = DATASET_DIR / filename
    if not path.exists():
        return {"dataset": f"evals/datasets/{filename}", "exists": False}
    raw = path.read_bytes()
    cases = sum(1 for line in raw.decode("utf-8").splitlines() if line.strip())
    return {
        "dataset": f"evals/datasets/{filename}",
        "exists": True,
        "cases": cases,
        "sha256": hashlib.sha256(raw).hexdigest()[:16],
    }


def model_fingerprint() -> dict:
    """模型底座指纹：换底座会改变所有指标，必须可对账。"""
    from infrastructure.config import get_value

    models: dict = {}
    for label, keys in _MODEL_KEYS:
        try:
            models[label] = get_value(*keys)
        except Exception:
            models[label] = None
    return models


def build_provenance(suites: dict[str, str], *, elapsed_s: float | None = None) -> dict:
    """构造 provenance 块。

    Args:
        suites: 评测项名 → 数据集文件名，如 {"intent": "intent.jsonl"}
        elapsed_s: 整轮评测墙钟耗时（秒），便于与 avg_ms 交叉核对。
    """
    prov: dict = {
        "schema": SCHEMA,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "git": git_fingerprint(),
        "host": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
        },
        "models": model_fingerprint(),
        "suites": {name: dataset_fingerprint(fn) for name, fn in suites.items()},
        "eval_elapsed_s": round(elapsed_s, 1) if elapsed_s is not None else None,
        "reproduce": "envs\\lunjiang\\python.exe -m evals.harness " + " ".join(suites),
    }
    return prov


def summarize_provenance(prov: dict) -> str:
    """把 provenance 压成一行人类可读摘要，供评测末尾打印与页面标注引用。"""
    g = prov.get("git", {})
    dirty = "（含未提交改动）" if g.get("dirty") else ""
    suites = " / ".join(
        f"{name} {info.get('cases', '?')} 条 sha256:{info.get('sha256', '?')}"
        for name, info in (prov.get("suites") or {}).items()
    )
    return (f"{prov.get('generated_at', '?')} | git {g.get('revision', '?')}{dirty} "
            f"| {suites}")
