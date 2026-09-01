#!/usr/bin/env python3
"""
ROUND10 · L-1 体积优化
----------------------
将 frontend/public/bg/ 下的 3 张主题图（PNG）转为 WebP，质量 82，method=6（最慢但最省）。

为什么用 WebP：
  - 同等质量体积约为 PNG 的 25-40%（节省 60-75%）
  - 浏览器支持率 ~97%（2024 caniuse），本项目为个人作品集可接受
  - PIL 自带 WebP 编码器，零新依赖

为什么不删原 PNG：
  - 保留为 _backup/<name>.png，万一需要回退可一行切回
  - 后续可走 git rm -r frontend/public/bg/_backup 等到稳态再清理
"""
import os
import sys
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BG_DIR = PROJECT_ROOT / 'public' / 'bg'
BACKUP = BG_DIR / '_backup'

# 3 张主题图 PNG → WebP（quality, method）
MAPPING = [
    ('bg-a-soft.png',     'bg-a-soft.webp',     82),
    ('bg-b-inkwash.png',  'bg-b-inkwash.webp',  82),
    ('bg-c-nightgold.png', 'bg-c-nightgold.webp', 82),
]


def main() -> int:
    BACKUP.mkdir(exist_ok=True)
    print(f'BG 目录: {BG_DIR}')
    print(f'Backup 目录: {BACKUP}')
    print(f'{"":-<60}')

    total_in = 0
    total_out = 0

    for src_name, dst_name, quality in MAPPING:
        src = BG_DIR / src_name
        dst = BG_DIR / dst_name

        if not src.exists():
            print(f'⚠ 跳过 {src_name}：源文件不存在')
            continue

        # 原 PNG 移到 backup 目录
        bkp = BACKUP / src_name
        if not bkp.exists():
            src.rename(bkp)
            print(f'  backup: {src_name} → _backup/')

        # 读 backup 后转 webp（保证我们工作在备份上）
        img = Image.open(bkp).convert('RGB')
        # 对 4K 原图缩到 1920 宽（v9 shanshui-mist.jpg 已用过 1920 宽），
        # 透明主题图改成白底（webp 不支持 alpha 或 RGB 选择其一）
        # 这里源都是 RGB 所以无需额外处理
        out_w = min(img.size[0], 1920)
        if img.size[0] > out_w:
            ratio = out_w / img.size[0]
            out_h = int(img.size[1] * ratio)
            img = img.resize((out_w, out_h), Image.LANCZOS)

        # method=6 = 最慢但最小；quality=82 = 视觉无损临界点
        img.save(dst, 'WEBP', quality=quality, method=6)

        in_kb = bkp.stat().st_size / 1024
        out_kb = dst.stat().st_size / 1024
        ratio = 100 * dst.stat().st_size / bkp.stat().st_size
        total_in += in_kb
        total_out += out_kb

        print(f'  ✓ {src_name} ({img.size[0]}x{img.size[1]}) q={quality}')
        print(f'      PNG: {in_kb:>7.1f} KB → WebP: {out_kb:>7.1f} KB  ({ratio:>5.1f}%)')

    print(f'{"":-<60}')
    print(f'合计: {total_in/1024:.2f} MB → {total_out/1024:.2f} MB（节省 {100*(1-total_out/total_in):.1f}%）')

    # 验证：所有 webp 都生成了
    missing = [n for _, n, _ in MAPPING if not (BG_DIR / n).exists()]
    if missing:
        print(f'❌ 失败：以下 webp 未生成: {missing}')
        return 1

    print(f'✓ 全部 {len(MAPPING)} 张主题图已转 webp')
    return 0


if __name__ == '__main__':
    sys.exit(main())
