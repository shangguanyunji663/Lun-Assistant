"""RAG 阶段三：交叉编码器精排（bge-reranker，sentence-transformers 本地加载）。"""
import logging
import os
import threading
from pathlib import Path

from app.config import get_value

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

    @classmethod
    def _get_model(cls):
        with cls._lock:
            if cls._model is None:
                name = get_value("rerank", "model", default="BAAI/bge-reranker-base")
                _set_offline_if_cached(name)
                from sentence_transformers import CrossEncoder
                device = get_value("rerank", "device", default="cpu")
                logger.info("加载交叉编码器 %s (%s)...", name, device)
                cls._model = CrossEncoder(name, device=device,
                                          max_length=int(get_value("rerank", "max_length", default=512)))
            return cls._model

    def rerank(self, query: str, candidates: list[dict], top_k: int = 5,
               alt_query: str | None = None) -> list[dict]:
        """交叉编码器精排；alt_query 提供时对每个候选双查询打分取最大值，
        防止改写漂移污染精排排序（原查询 = 用户真实意图的最忠实表达）。"""
        if not candidates:
            return []
        model = self._get_model()
        scores = model.predict([(query, c["content"]) for c in candidates])
        if alt_query and alt_query != query:
            alt_scores = model.predict([(alt_query, c["content"]) for c in candidates])
            scores = [max(s, sa) for s, sa in zip(scores, alt_scores)]
        for c, s in zip(candidates, scores):
            c["rerank_score"] = float(s)
        ranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
        return ranked[:top_k]


reranker = Reranker()
