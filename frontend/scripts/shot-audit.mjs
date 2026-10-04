/* 本次改动的截图验证：字体自托管是否生效 / boot 态 / 按下态 / 骨架屏所在面板。
   复用项目脚本的 playwright-core 引用方式；app 用 ?demo=1 免登录（仅 DEV 生效）。 */
import { chromium } from 'file:///C:/Users/17536/.workbuddy/binaries/node/workspace/node_modules/playwright-core/index.mjs'

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const BASE = 'http://127.0.0.1:5173/'
const OUT = 'D:/PythonProject/Lun-Assistant/frontend/_audit-shots'

const browser = await chromium.launch({ executablePath: CHROME, args: ['--no-proxy-server', '--disable-gpu'] })
const page = await browser.newPage({ viewport: { width: 1600, height: 900 } })

const gfonts = []
const woff2 = []
page.on('request', (r) => {
  const u = r.url()
  if (u.includes('fonts.googleapis.com') || u.includes('fonts.gstatic.com')) gfonts.push(u)
  if (u.endsWith('.woff2') || u.endsWith('.woff')) woff2.push(u)
})
const errors = []
page.on('pageerror', (e) => errors.push('pageerror: ' + e.message))

// 1. 工作台皮肤 A（demo 模式免登录）
await page.goto(BASE + 'app.html?demo=1', { waitUntil: 'networkidle' })
await page.evaluate(() => document.fonts.ready)
await page.waitForTimeout(900)
const fontCheck = await page.evaluate(() => ({
  sans900: document.fonts.check('900 40px "Noto Sans SC"'),
  serif900: document.fonts.check('900 40px "Noto Serif SC"'),
  plexMono: document.fonts.check('500 14px "IBM Plex Mono"'),
}))
await page.screenshot({ path: OUT + '/app-skin-a.png' })

// 2. 工作台皮肤 B（暗色，验证 tabular-nums / 气泡行宽不破版）
await page.evaluate(() => { localStorage.setItem('lj_skin', 'b') })
await page.goto(BASE + 'app.html?demo=1', { waitUntil: 'networkidle' })
await page.evaluate(() => document.fonts.ready)
await page.waitForTimeout(900)
await page.screenshot({ path: OUT + '/app-skin-b.png' })

// 3. 落地页（自托管字体 + favicon + 按下态所在页）
await page.evaluate(() => { localStorage.removeItem('lj_skin') })
await page.goto(BASE, { waitUntil: 'networkidle' })
await page.evaluate(() => document.fonts.ready)
await page.waitForTimeout(900)
await page.screenshot({ path: OUT + '/landing-a.png' })

console.log(JSON.stringify({ fontCheck, gfonts: gfonts.length, woff2: woff2.length, errors }, null, 2))
await browser.close()
