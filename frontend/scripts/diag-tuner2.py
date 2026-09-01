#!/usr/bin/env python3
"""像素级验证 tuner.html 滑杆是否真正驱动预览变化。"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

TUNER = Path(r'D:\PythonProject\Lun-Assistant\design-concepts\tuner.html')
CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
OUT = Path(r'D:\PythonProject\Lun-Assistant\docs\screenshots')

def shot(page, name):
    p = OUT / f'diag2-{name}.png'
    page.screenshot(path=str(p))
    return p

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME, headless=True,
            args=['--no-sandbox', '--disable-gpu', '--allow-file-access-from-files'])
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        errs = []
        page.on('pageerror', lambda e: errs.append(str(e)))
        page.goto(f'file:///{TUNER.as_posix()}', wait_until='load', timeout=15000)
        page.wait_for_timeout(1200)

        # 初始状态（op=0.14）
        p0 = shot(page, 'op-014-before')

        # 用 evaluate 正确设置滑杆 + 触发 input（range 不能 fill）
        page.locator('#s-op').evaluate("""(el) => {
          el.value = 0.30; el.dispatchEvent(new Event('input', {bubbles: true}));
        }""")
        page.wait_for_timeout(400)
        p1 = shot(page, 'op-030-after')

        # 读取实时显示值
        print('v-op 显示:', page.locator('#v-op').text_content())
        print('内容区有效不透明度:', page.locator('#m-eff').text_content())
        print('stage --p-op:', page.locator('.stage').evaluate("el => el.style.getPropertyValue('--p-op')"))

        # 再拖到 0.00（应完全纯色）
        page.locator('#s-op').evaluate("""(el) => {
          el.value = 0.00; el.dispatchEvent(new Event('input', {bubbles: true}));
        }""")
        page.wait_for_timeout(400)
        p2 = shot(page, 'op-000-none')

        # 像素差异对比（用 numpy 不装，改用 PIL 直方图差异）
        from PIL import Image
        def diff(a, b):
            ia, ib = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
            wa, ha = ia.size
            px_a, px_b = ia.load(), ib.load()
            total, changed = 0, 0
            for x in range(0, wa, 10):      # 抽样 1/10 像素，快
                for y in range(0, ha, 10):
                    total += 1
                    if px_a[x, y] != px_b[x, y]:
                        changed += 1
            return changed / max(total, 1) * 100

        print(f'\n=== 像素差异（抽样 10% 像素）===')
        print(f'op 0.14→0.30: 差异 {diff(p0, p1):.2f}%')
        print(f'op 0.30→0.00: 差异 {diff(p1, p2):.2f}%')

        if errs:
            print('\nJS 错误:', errs[:10])
        else:
            print('\n无 JS 错误')
        browser.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
