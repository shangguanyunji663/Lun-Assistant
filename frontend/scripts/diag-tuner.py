#!/usr/bin/env python3
"""诊断 tuner.html 调参台为何不生效：抓控制台错误 + 截图 + 检查滑杆交互。"""
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

TUNER = Path(r'D:\PythonProject\Lun-Assistant\design-concepts\tuner.html')
CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe'

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME,
            headless=True,
            args=['--no-sandbox', '--disable-gpu', '--allow-file-access-from-files'],
        )
        page = browser.new_page(viewport={'width': 1440, 'height': 900})

        # 收集 console 错误
        errors = []
        page.on('console', lambda m: errors.append(f'[{m.type}] {m.text}') if m.type == 'error' else None)
        page.on('pageerror', lambda e: errors.append(f'[pageerror] {e}'))

        # file:// 协议打开（与用户双击打开行为一致）
        page.goto(f'file:///{TUNER.as_posix()}', wait_until='load', timeout=15000)
        page.wait_for_timeout(1500)

        print('=== 控制台错误 ===')
        if errors:
            for e in errors[:15]:
                print(' ', e)
        else:
            print('  无 JS 错误')

        # 检查滑杆是否存在 + 拖动
        print('\n=== 滑杆检查 ===')
        for sid in ['s-op', 's-top', 's-mid', 's-wash', 's-grain', 's-kb']:
            exists = page.locator(f'#{sid}').count()
            print(f'  #{sid}: {"存在" if exists else "缺失!"}')

        # 截图初始状态
        page.screenshot(path=str(Path(r'D:\PythonProject\Lun-Assistant\docs\screenshots\diag-tuner-initial.png')))
        print('\n已截初始图: docs/screenshots/diag-tuner-initial.png')

        # 尝试拖动 op 滑杆
        print('\n=== 拖动 op 滑杆 0.14 -> 0.30 ===')
        try:
            page.locator('#s-op').fill('0.30')  # fill 对 range 可能不生效，改用 evaluate
            page.locator('#s-op').evaluate("(el) => { el.value = 0.30; el.dispatchEvent(new Event('input', {bubbles:true})); }")
            page.wait_for_timeout(300)
            val = page.locator('#v-op').text_content()
            eff = page.locator('#m-eff').text_content()
            print(f'  v-op 显示值: {val}')
            print(f'  内容区有效不透明度: {eff}')
            # 检查 stage 上 CSS 变量
            pval = page.locator('.stage').evaluate("(el) => el.style.getPropertyValue('--p-op')")
            print(f'  stage.style --p-op: {pval}')
        except Exception as e:
            print(f'  拖动异常: {e}')

        # 检查 ink-photo 的背景图是否加载
        print('\n=== 背景图加载状态 ===')
        img_state = page.locator('.ink-photo').evaluate("""(el) => {
            const bg = getComputedStyle(el).backgroundImage;
            const img = new Image();
            const urlMatch = bg.match(/url\\(['\"]?(.*?)['\"]?\\)/);
            return { backgroundImage: bg, url: urlMatch ? urlMatch[1] : null };
        }""")
        print(f'  backgroundImage: {img_state["backgroundImage"]}')
        if img_state['url']:
            # 检查图片是否可访问
            ok = page.evaluate("""(url) => new Promise(res => {
                const img = new Image();
                img.onload = () => res('加载成功');
                img.onerror = () => res('加载失败 (404/路径错)');
                img.src = url;
            })""", img_state['url'])
            print(f'  图片URL: {img_state["url"]} → {ok}')

        # 检查主题切换 tab
        print('\n=== 主题切换 tab ===')
        tabs = page.locator('.theme-tabs [data-theme]').count()
        print(f'  主题 tab 数: {tabs}')
        page.locator('.theme-tabs [data-theme="c"]').click()
        page.wait_for_timeout(400)
        theme = page.locator('body').get_attribute('data-theme')
        print(f'  点击 C 后 body[data-theme] = {theme}')
        page.screenshot(path=str(Path(r'D:\PythonProject\Lun-Assistant\docs\screenshots\diag-tuner-theme-c.png')))

        browser.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
