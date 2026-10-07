"""临时审计脚本：校验全仓 Markdown 内部链接是否指向真实存在的文件。

用途：文档同步后验证「内部链接仍然有效」这一验收条件。
只检查相对路径链接（含 .md/.py/.yml 等扩展名或显式路径），跳过 http(s)、mailto 与纯锚点。

注意：**代码围栏内的链接一律跳过**。历史轮次档案里常见 ```diff 块记录
"当时对 README 的改动"，其中路径相对仓库根而非相对该文档 —— 那不是死链。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"node_modules", "envs", ".git", "dist", "__pycache__",
             ".pytest_cache", ".ruff_cache", ".mypy_cache"}
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
FENCE = re.compile(r"^\s*(```|~~~)")


def prose_lines(lines: list[str]):
    """产出 (行号, 行内容)，跳过代码围栏内的行。"""
    in_fence = False
    for lineno, line in enumerate(lines, 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield lineno, line


problems: list[tuple[str, int, str]] = []
checked = 0
skipped_in_fence = 0

for md in sorted(ROOT.rglob("*.md")):
    rel_parts = set(md.relative_to(ROOT).parts)
    if rel_parts & SKIP_DIRS:
        continue
    try:
        lines = md.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        continue
    for lineno, line in prose_lines(lines):
        for raw in LINK.findall(line):
            target = raw.strip().split("#")[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if not re.search(r"\.[A-Za-z0-9]{1,6}$|/", target):
                continue
            checked += 1
            resolved = (md.parent / target).resolve()
            if not resolved.exists():
                problems.append((str(md.relative_to(ROOT)), lineno, target))

print(f"检查正文相对链接 {checked} 条（已跳过代码围栏内的示例链接），死链 {len(problems)} 条")
for path, lineno, target in problems:
    print(f"  DEAD {path}:{lineno} -> {target}")
if not problems:
    print("  ✅ 全部内部链接有效")
sys.exit(0)
