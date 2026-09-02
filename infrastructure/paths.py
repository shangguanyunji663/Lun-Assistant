"""项目路径常量（单一真源）。

背景：此前 `PROJECT_ROOT` 在 12 处重复定义（`Path(__file__).resolve().parent.parent`，
层级随文件深度各异，极易写错），`sys.path.insert` 引导样板散落在 scripts/ 与 evals/ 下 12 处。

本模块收敛路径语义：所有业务代码一律从此处导入 PROJECT_ROOT / CONFIG_DIR / DATA_DIR / EVALS_DIR，
不再各自计算。可执行脚本（scripts/、evals/）的 sys.path 引导样板仍需保留一行，
但仅用于将项目根加入搜索路径，路径常量本身不再重复定义。
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "configs"
DATA_DIR = PROJECT_ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
CORPUS_DIR = DATA_DIR / "corpus"
EVALS_DIR = PROJECT_ROOT / "evals"
EVALS_DATASETS_DIR = EVALS_DIR / "datasets"

__all__ = [
    "CONFIG_DIR",
    "CORPUS_DIR",
    "DATA_DIR",
    "EVALS_DATASETS_DIR",
    "EVALS_DIR",
    "PROJECT_ROOT",
    "UPLOADS_DIR",
]
