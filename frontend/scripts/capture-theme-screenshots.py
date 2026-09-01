#!/usr/bin/env python3
"""
ROUND9 L-8 · 三主题切换截图脚本
---------------------------------
用 Playwright + 系统浏览器（Chrome 或 Edge）截图 dist/index.html 的三主题（A/B/C）状态。

为什么用系统浏览器而不是 playwright 内置 chromium：
  - 用户电脑已装 Chrome（默认）和 Edge，二者均可直接调用
  - 节省下载 chromium 内核（~200 MB）
  - Edge 启动速度比 Chrome 略快 + 用户数据隔离更稳

CLI:
    python capture-theme-screenshots.py                  # 默认 Chrome
    python capture-theme-screenshots.py --browser edge    # 用 Edge
"""
import argparse
import http.server
import os
import socketserver
import sys
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DIST = PROJECT_ROOT / 'frontend' / 'dist'
OUT = PROJECT_ROOT / 'docs' / 'screenshots'
CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
PORT = 4173
URL = f'http://127.0.0.1:{PORT}/'

THEMES = [
    ('a', 'soft-blue',   'A 柔雾青蓝'),
    ('b', 'ink-wash',    'B 水墨留白'),
    ('c', 'night-gold',  'C 暗墨柔化'),
]

BROWSER_PATHS = {
    'chrome': CHROME,
    'edge': EDGE,
}

BROWSER_CHANNELS = {
    'chrome': 'chrome',
    'edge': 'msedge',
}


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def serve_dist():
    os.chdir(str(DIST))
    httpd = socketserver.TCPServer(('127.0.0.1', PORT), QuietHandler)
    httpd.allow_reuse_address = True
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def main() -> int:
    parser = argparse.ArgumentParser(description='截三主题（A/B/C）预览图')
    parser.add_argument('--browser', choices=['chrome', 'edge'], default='chrome',
                        help='用哪个浏览器（默认 chrome）')
    parser.add_argument('--subdir', default=None,
                        help='截图输出子目录（默认按浏览器命名：chrome/edge）')
    args = parser.parse_args()

    if not DIST.exists():
        print(f'❌ dist 不存在: {DIST}')
        print('请先 npm run build')
        return 1

    subdir = args.subdir or args.browser
    out_dir = OUT / subdir
    out_dir.mkdir(exist_ok=True, parents=True)
    print(f'输出目录: {out_dir}')
    print(f'浏览器: {args.browser} ({BROWSER_PATHS[args.browser]})')

    httpd = serve_dist()
    print(f'静态服务: {URL}')
    time.sleep(0.5)

    try:
        with sync_playwright() as p:
            launch_kwargs = dict(headless=True,
                                 args=['--no-sandbox', '--disable-gpu',
                                       '--disable-dev-shm-usage'])

            # Edge 单独指定 user-data-dir 避免与日常 Edge 浏览冲突
            use_persistent = (args.browser == 'edge')
            if use_persistent:
                launch_kwargs['chromium_sandbox'] = False

            try:
                if use_persistent:
                    # Edge 必须用 launch_persistent_context 才能传 user_data_dir
                    udd = str(PROJECT_ROOT / '.workbuddy' / 'edge-screenshot-profile')
                    os.makedirs(udd, exist_ok=True)
                    ctx = p.chromium.launch_persistent_context(
                        user_data_dir=udd,
                        executable_path=BROWSER_PATHS[args.browser],
                        headless=True,
                        device_scale_factor=1.5,  # 高清（Chrome 等同）
                        args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
                    )
                    print(f'✓ 启动系统 Edge (launch_persistent_context, udd={udd})')
                    page = ctx.new_page()
                    browser = None
                else:
                    browser = p.chromium.launch(channel=BROWSER_CHANNELS[args.browser],
                                                  **launch_kwargs)
                    print(f'✓ 启动系统 {args.browser} (channel="{BROWSER_CHANNELS[args.browser]}")')
                    page = None
            except Exception as e:
                print(f'⚠ channel 失败 ({e}); 回退到 executable_path')
                browser = p.chromium.launch(executable_path=BROWSER_PATHS[args.browser],
                                              **launch_kwargs)
                print(f'✓ 启动系统 {args.browser} (executable_path)')
                page = None

            if page is None:
                if browser is None:
                    return 1
                page = browser.new_page(viewport={'width': 1440, 'height': 900},
                                        device_scale_factor=1.5)
            else:
                page.set_viewport_size({'width': 1440, 'height': 900})
                # Edge 走 launch_persistent_context，device_scale_factor 已在 context 里设 1.5
            page.goto(URL, wait_until='domcontentloaded', timeout=15000)
            page.wait_for_timeout(1200)

            page.screenshot(path=str(out_dir / 'login-A-soft-blue.png'), full_page=False)
            print(f'  ✓ login-A-soft-blue.png')

            page.evaluate("""
                localStorage.setItem('lj_token', 'fake-token-for-screenshot');
                localStorage.setItem('lj_user', JSON.stringify({username: 'wgw', role: 'student'}));
            """)

            for tid, slug, label in THEMES:
                page.evaluate(f"localStorage.setItem('lj_theme', '{tid}')")
                page.reload(wait_until='domcontentloaded')
                page.wait_for_timeout(1500)
                out_path = out_dir / f'main-{tid}-{slug}.png'
                page.screenshot(path=str(out_path), full_page=False)
                print(f'  ✓ main-{tid}-{slug}.png  ({label})')

            browser.close() if browser else ctx.close()
    finally:
        httpd.shutdown()

    print(f'\n✓ 全部截图已保存到 {out_dir}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
