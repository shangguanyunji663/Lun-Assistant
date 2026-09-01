"""P2 并发压测：知识库检索端点 QPS / 延迟 P95 / 服务端内存采样。

用法（需 uvicorn 已启动 + Ollama 在线）：
    envs\\lunjiang\\python.exe scripts/load_test.py --concurrency 8 --total 40

流程：注册临时用户 → 建项目 → 上传样例文档 → 并发打 /knowledge/search
→ 统计 QPS / P50 / P95 / 成功率 → 采样服务进程内存 → 输出 evals/load_report.json
"""
import argparse
import asyncio
import json
import logging
import statistics
import time
from pathlib import Path

import httpx

logging.basicConfig(level=logging.WARNING)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE = "http://127.0.0.1:8000"
SAMPLE = ("# 压测文档\n\n混合检索与交叉编码器精排技术：密集检索通过向量相似度召回候选，"
          "稀疏检索利用 BM25 词频建模，二者经倒数排名融合后由交叉编码器精排。"
          "项目级知识库支持多格式文档上传并自动分块入库。\n" * 12)


def _server_pid(url: str) -> int | None:
    try:
        import psutil
        host = url.split("://")[1].split(":")[0]
        port = int(url.split(":")[2].split("/")[0]) if ":" in url.split("://")[1] else 8000
        for conn in psutil.net_connections(kind="tcp"):
            if conn.status == "LISTEN" and conn.laddr.port == port and conn.laddr.ip in ("0.0.0.0", "127.0.0.1"):
                return conn.pid
    except Exception:
        return None
    return None


def _sample_memory(pid: int | None, seconds: float) -> dict:
    if pid is None:
        return {"sampled": False, "reason": "psutil 未安装或未找到服务进程"}
    try:
        import psutil
        proc = psutil.Process(pid)
        import time as _t
        base = proc.memory_info().rss / 1024 / 1024
        samples = [base]
        end = _t.time() + seconds
        while _t.time() < end:
            samples.append(proc.memory_info().rss / 1024 / 1024)
            _t.sleep(0.5)
        # 含子进程（uvicorn worker）
        for ch in proc.children(recursive=True):
            try:
                samples.append(ch.memory_info().rss / 1024 / 1024)
                del ch
            except Exception:
                pass
        return {"sampled": True, "rss_mb_baseline": round(base, 1),
                "rss_mb_peak": round(max(samples), 1),
                "rss_mb_growth": round(max(samples) - base, 1)}
    except Exception as e:
        return {"sampled": False, "reason": str(e)[:120]}


async def _setup() -> tuple[str, int, str]:
    """注册临时用户 → 建项目 → 上传文档 → 返回 (token, project_id, doc_content_terms)。"""
    import time as _t
    uname = f"load{int(_t.time() * 1000)}"
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(f"{BASE}/api/auth/register",
                         json={"username": uname, "password": "loadtest123"})
        r.raise_for_status()
        token = (await c.post(f"{BASE}/api/auth/login",
                              json={"username": uname, "password": "loadtest123"})).json().get("access_token")
        h = {"Authorization": f"Bearer {token}"}
        pid = (await c.post(f"{BASE}/api/projects", headers=h,
                            json={"title": "__load__"})).json()["id"]
        await c.post(f"{BASE}/api/projects/{pid}/knowledge", headers=h,
                     files={"files": ("sample.md", SAMPLE.encode("utf-8"), "text/markdown")})
        return token, pid, uname


async def _fire(client: httpx.AsyncClient, headers: dict, pid: int) -> tuple[float, bool]:
    t0 = time.perf_counter()
    try:
        r = await client.post(f"{BASE}/api/projects/{pid}/knowledge/search",
                              headers=headers,
                              json={"query": "混合检索精排技术 项目知识库入库", "top_k": 5,
                                    "mode": "project"})
        return (time.perf_counter() - t0) * 1000, r.status_code == 200
    except Exception:
        return (time.perf_counter() - t0) * 1000, False


async def main() -> int:
    ap = argparse.ArgumentParser(description="知识库检索并发压测")
    ap.add_argument("--url", default=BASE)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--total", type=int, default=40)
    args = ap.parse_args()

    print(f"[1/5] 初始化（注册+建库+上传样例）…")
    token, pid, _ = await _setup()
    headers = {"Authorization": f"Bearer {token}"}

    lat: list[float] = []
    ok = 0
    done = 0
    sem = asyncio.Semaphore(args.concurrency)

    async def worker():
        nonlocal ok, done
        async with httpx.AsyncClient(timeout=120) as c:
            for _ in range(args.total):
                async with sem:
                    dt, success = await _fire(c, headers, pid)
                    lat.append(dt)
                    done += 1
                    ok += 1 if success else 0

    print(f"[2/5] 压测中：并发={args.concurrency} 总请求={args.total}")
    t0 = time.perf_counter()
    await asyncio.gather(*[worker() for _ in range(args.concurrency)])
    elapsed = time.perf_counter() - t0

    qps = done / elapsed
    p50 = statistics.median(lat) if lat else 0
    lat_sorted = sorted(lat)
    p95 = lat_sorted[min(len(lat_sorted) - 1, int(len(lat_sorted) * 0.95))] if lat else 0
    rate = ok / done if done else 0

    print(f"[3/5] 结果：实际请求={done} QPS={qps:.1f} P50={p50:.0f}ms P95={p95:.0f}ms 成功率={rate * 100:.1f}%")
    print(f"[4/5] 内存采样中（服务进程，约8s）…")
    mem = _sample_memory(_server_pid(args.url), seconds=8)

    report = {
        "endpoint": f"{args.url}/api/projects/{{id}}/knowledge/search",
        "concurrency": args.concurrency, "total": args.total,
        "elapsed_s": round(elapsed, 2), "qps": round(qps, 1),
        "latency_ms": {"p50": round(p50), "p95": round(p95), "max": round(max(lat or [0]))},
        "success_rate": round(rate, 4),
        "memory_mb": mem,
        "note": "检索含 bge-m3 稠密路（本地CPU）+ 精排；QPS 受限于本地嵌入/精排吞吐",
    }
    out = PROJECT_ROOT / "evals" / "load_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[5/5] 报告已写入 {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))