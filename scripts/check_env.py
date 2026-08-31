"""阶段0 连通性验证脚本。

验证项：
1. Ollama 对话模型（qwen3:4b，关闭思考模式取快速回复）
2. Ollama Embedding（bge-m3）
3. Redis 读写
4. PostgreSQL 连接 + 自动建库(lunjiang) + pgvector 扩展

用法：python scripts/check_env.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import httpx  # noqa: E402
import psycopg  # noqa: E402
import redis  # noqa: E402

from app.config import get_settings  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    mark = "PASS" if ok else "FAIL"
    suffix = f" | {detail}" if detail else ""
    print(f"[{mark}] {name}{suffix}")


def check_ollama_chat(base_url: str, model: str) -> None:
    root = base_url.replace("/v1", "")
    resp = httpx.post(
        f"{root}/api/generate",
        json={"model": model, "prompt": "只回复两个字母: OK", "think": False,
              "stream": False, "options": {"num_predict": 16}},
        timeout=120,
    )
    resp.raise_for_status()
    text = resp.json().get("response", "").strip()
    record("Ollama 对话模型", bool(text), f"{model} -> {text[:40]!r}")


def check_ollama_embedding(base_url: str, model: str) -> None:
    root = base_url.replace("/v1", "")
    resp = httpx.post(f"{root}/api/embed", json={"model": model, "input": "论文选题分析"},
                      timeout=60)
    resp.raise_for_status()
    dim = len(resp.json()["embeddings"][0])
    record("Ollama Embedding", dim > 0, f"{model} 向量维度={dim}")


def check_redis(url: str) -> None:
    r = redis.Redis.from_url(url, decode_responses=True)
    pong = r.ping()
    r.set("lunjiang:check", "ok", ex=30)
    val = r.get("lunjiang:check")
    record("Redis", pong and val == "ok", f"PING={pong}, SET/GET={val}")


def check_postgres(sync_dsn: str) -> None:
    """先连 postgres 系统库确保目标库存在，再验证 pgvector。"""
    admin_dsn = sync_dsn.rsplit("/", 1)[0] + "/postgres"
    db_name = sync_dsn.rsplit("/", 1)[1].split("?")[0]
    with psycopg.connect(admin_dsn, autocommit=True) as conn:
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,)).fetchone()
        if not exists:
            conn.execute(f'CREATE DATABASE "{db_name}"')
            record("PostgreSQL 建库", True, f"已创建数据库 {db_name}")
        else:
            record("PostgreSQL 连接", True, f"数据库 {db_name} 已存在")

    with psycopg.connect(sync_dsn, autocommit=True) as conn:
        ext = conn.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'").fetchone()
        if not ext:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            ext = conn.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'").fetchone()
        record("pgvector 扩展", bool(ext), "vector 类型可用" if ext else "CREATE EXTENSION 失败")


def main() -> int:
    cfg = get_settings()
    provider = cfg["llm"]["default_provider"]
    prov = cfg["llm"]["providers"][provider]
    print(f"== 论匠环境检查（LLM provider: {provider}）==\n")

    check_ollama_chat(prov["base_url"], prov["chat_model"])
    if prov.get("embedding_model"):
        check_ollama_embedding(prov["base_url"], prov["embedding_model"])
    check_redis(cfg["storage"]["redis"]["url"])
    check_postgres(cfg["storage"]["postgres"]["sync_dsn"])

    failed = [n for n, ok, _ in RESULTS if not ok]
    print(f"\n结果: {len(RESULTS) - len(failed)}/{len(RESULTS)} 通过" + (f"，失败项: {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
