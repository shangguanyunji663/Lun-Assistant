"""RAG 纯逻辑单测：RRF 融合 / 拒答识别 / 降噪标记（离线，不触库）。"""
from services.rag.pipeline import _is_rejection, _noise_penalty
from services.rag.retriever import HybridRetriever


def _hit(i, **kw):
    return {"id": i, "content": kw.get("content", f"c{i}"), "meta": kw.get("meta", {})}


def test_rrf_fuse_fuses_and_ranks():
    a = [_hit(1), _hit(2), _hit(3)]
    b = [_hit(2), _hit(1)]
    fused = HybridRetriever.rrf_fuse(a, b, top_k=3)
    ids = [x["id"] for x in fused]
    assert 1 in ids and 2 in ids
    # 同时被两路命中的 id 得分更高
    scores = {x["id"]: x["rrf_score"] for x in fused}
    assert scores[1] > scores[3]


def test_rrf_fuse_empty():
    assert HybridRetriever.rrf_fuse() == []


def test_is_rejection():
    assert _is_rejection("无法改写该内容")
    assert _is_rejection("短")
    assert not _is_rejection("大模型注意力机制综述 检索")


def test_noise_penalty_marks_sparse_only():
    fused = [_hit(10), _hit(20)]
    _noise_penalty(fused, dense_ids={10}, sparse_ids={20}, dense_rank={10: 1})
    by_id = {x["id"]: x for x in fused}
    assert by_id[10]["noise_flag"] == "ok"
    assert by_id[20]["noise_flag"] == "sparse_only"
    assert by_id[20]["rerank_boost"] < 1.0
