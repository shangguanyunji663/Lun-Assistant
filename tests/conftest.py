"""pytest 全局配置：路径注入 + Windows 事件循环策略。

历史说明：以前 evals/ 与 scripts/ 各自重复 sys.path.insert；测试侧统一收敛到本
conftest，业务模块路径常量统一来自 infrastructure/paths.py。
"""
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform == "win32":
    # asyncpg / psycopg 异步连接需要 Selector 事件循环（Windows 默认 Proactor 不支持）
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
