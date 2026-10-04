"""启动前快检（秒级、只读、不建表、不调 LLM）。

与 check_env.py（深检：真实调用 5 项，需依赖全起）互补 —— 本脚本回答
「现在能不能起后端」，逐项给出人话修复指引。dev_up.ps1 末尾会自动调用。

用法：envs\\lunjiang\\python.exe scripts/preflight.py
"""
import json
import socket
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CHAT_MODEL = "qwen3:4b-ctx4096"
EMBED_MODEL = "bge-m3"

issues: list[str] = []


def ok(name: str, detail: str = "") -> None:
    suffix = f" | {detail}" if detail else ""
    print(f"[PASS] {name}{suffix}")


def fail(name: str, fix: str) -> None:
    print(f"[FAIL] {name} → {fix}")
    issues.append(name)


def port_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex(("127.0.0.1", port)) == 0


def read_env() -> dict[str, str]:
    """极简 .env 读取：只取 KEY=VALUE，供端口口径核对。"""
    env: dict[str, str] = {}
    p = ROOT / ".env"
    if not p.exists():
        return env
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def main() -> int:
    env = read_env()
    pg_port = int(env.get("PG_PORT", "5433"))
    redis_port = int(env.get("REDIS_PORT", "6379"))

    # 1) 虚拟环境
    if (ROOT / "envs" / "lunjiang" / "python.exe").exists():
        ok("Python 虚拟环境", "envs\\lunjiang")
    else:
        fail("Python 虚拟环境", "先完成 README 第 0 步 0.2：conda create -p envs\\lunjiang python=3.11 -y")

    # 2) .env 与端口口径
    if env:
        ok(".env 存在")
        if pg_port == 5432:
            fail(".env 端口口径", "PG_PORT=5432 是本项目最常见启动报错来源——全仓库口径是 5433，请改 .env")
        else:
            ok(".env 端口口径", f"PG_PORT={pg_port}")
    else:
        fail(".env", "copy .env.example .env（第 0 步 0.3），原生 PG 记得改 PG_PASSWORD")

    # 3) 三个依赖端口
    if port_open(pg_port):
        ok("PostgreSQL 端口", f"127.0.0.1:{pg_port} 监听中")
    else:
        fail("PostgreSQL 端口", f"{pg_port} 无监听。起 PG：README 第 1 步，或 scripts\\dev_up.ps1 -infra-only")

    if port_open(redis_port):
        ok("Redis 端口", f"127.0.0.1:{redis_port} 监听中")
    else:
        fail("Redis 端口", f"{redis_port} 无监听。起 Redis：redis-server（第 1 步 2)）。"
                        "注意：Redis 缺失不会报错，但短期记忆/限流/锁会静默降级")

    ollama_up = port_open(11434)
    if ollama_up:
        ok("Ollama 端口", "127.0.0.1:11434 监听中")
    else:
        fail("Ollama 端口", "11434 无监听。新开窗口执行 ollama serve（第 1 步 3)）")

    # 4) Ollama 模型清单（顺带核对两个镜像是否已 pull/create）
    if ollama_up:
        try:
            with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as resp:
                models = {m.get("name", "") for m in json.load(resp).get("models", [])}
            if CHAT_MODEL in models:
                ok("对话模型镜像", CHAT_MODEL)
            else:
                fail("对话模型镜像", f"未找到 {CHAT_MODEL} → ollama pull qwen3:4b && "
                                    f"ollama create {CHAT_MODEL} -f configs\\ollama\\Modelfile.qwen3-ctx4096（第 0 步 0.4）")
            if EMBED_MODEL in models:
                ok("嵌入模型", EMBED_MODEL)
            else:
                fail("嵌入模型", f"未找到 {EMBED_MODEL} → ollama pull {EMBED_MODEL}（第 0 步 0.4）")
        except Exception as exc:  # 快检容错：任何异常都只记失败不中断
            fail("Ollama 模型清单", f"/api/tags 查询失败（{exc}），确认 ollama serve 正常后重试")

    print(f"\n结果: {'可启动，全部通过' if not issues else f'{len(issues)} 项待修复：{issues}'}")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
