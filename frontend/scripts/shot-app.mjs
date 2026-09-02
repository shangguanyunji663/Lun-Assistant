/* 主应用验证脚本：mock 登录 API，逐个切换 4 主题并截图。
   用途：验证用户实际 npm run dev 打开的主界面渲染出 4 主题，配色随参考图。 */
import { chromium } from 'file:///C:/Users/17536/.workbuddy/binaries/node/workspace/node_modules/playwright-core/index.mjs'

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const BASE = 'http://localhost:5173/' // dev server base='/'（Vite 默认绑 ::1）
const OUT = 'D:\\PythonProject\\Lun-Assistant\\frontend\\_theme-shots'

const THEMES = [
  { id: 'a', name: 'App-A-柔雾青绿' },
  { id: 'b', name: 'App-B-水墨留白' },
  { id: 'c', name: 'App-C-暗墨夜山' },
  { id: 'd', name: 'App-D-青绿金碧' },
]

const browser = await chromium.launch({ executablePath: CHROME, args: ['--no-proxy-server', '--disable-gpu'] })
const page = await browser.newPage({ viewport: { width: 1600, height: 900 } })

const errors = []
page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`))
page.on('console', (m) => { if (m.type() === 'error' && !m.text().includes('favicon')) errors.push(`console: ${m.text()}`) })

// 拦截后端 API：无后端也能进入主界面
await page.route('**/api/auth/me', (r) => r.fulfill({
  status: 200, contentType: 'application/json',
  body: JSON.stringify({ id: 1, username: '演示用户', role: 'admin' }),
}))
await page.route('**/api/projects', (r) => r.fulfill({
  status: 200, contentType: 'application/json', body: '[]',
}))
await page.addInitScript(() => { try { localStorage.setItem('lj_token', 'mock-token') } catch {} })

await page.goto(BASE, { waitUntil: 'networkidle' })
try {
  await page.waitForSelector('.theme-tabs', { timeout: 20000 })
  console.log('✓ 主界面 .theme-tabs 已渲染')
} catch {
  console.log('✗ .theme-tabs 未出现。当前页面片段：')
  console.log((await page.locator('body').innerText()).slice(0, 300))
  await page.screenshot({ path: `${OUT}\\App-登录页-调试.png` })
}

// 主题 tab 断言
const tabs = await page.$$eval('.theme-tabs button', (els) =>
  els.map((el) => ({ theme: el.dataset.theme, label: el.textContent.trim().replace(/\s+/g, ' '), sel: el.classList.contains('on') }))
)
console.log('主应用主题 tab:', JSON.stringify(tabs, null, 2))

// 主界面结构断言：body[data-theme] 是否正确设置
for (const t of THEMES) {
  // 优先点按钮；若未登录没有按钮则直接设置 body dataset（已登录场景应走点击）
  const btn = page.locator(`.theme-tabs button[data-theme="${t.id}"]`)
  if (await btn.count()) {
    await btn.click()
    await page.waitForTimeout(700) // 过渡 + 音效延迟
  } else {
    await page.evaluate((th) => { document.body.dataset.theme = th }, t.id)
    await page.waitForTimeout(500)
  }
  const probe = await page.evaluate(() => {
    const cs = getComputedStyle(document.body)
    const vars = ['--bg-deep', '--ink-hi', '--jade', '--gold', '--bg-rgb']
    const o = { theme: document.body.dataset.theme, bgColor: cs.backgroundColor }
    vars.forEach((v) => { o[v] = cs.getPropertyValue(v).trim() })
    // 背景图（若 .ink-photo 存在）
    const ph = document.querySelector('.ink-photo')
    o.photo = ph ? getComputedStyle(ph).backgroundImage.slice(0, 70) : '(无 ink-photo)'
    return o
  })
  console.log(`\n[${t.name}]`, JSON.stringify(probe))
  await page.screenshot({ path: `${OUT}\\${t.name}.png` })
}

if (errors.length) { console.log('\n页面错误:'); errors.forEach((e) => console.log('  ', e)) }
else console.log('\n无页面错误（favicon 除外）')

await browser.close()
