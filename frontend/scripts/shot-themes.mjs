/* 主题截图脚本：用系统 Chrome 打开调参台，逐个切换 4 主题并截图。
   用途：人工核对四主题配色 / 背景图是否与参考图一致。 */
// playwright-core 装在隔离 workspace，用绝对路径导入（ESM 不读 NODE_PATH）
import { chromium } from 'file:///C:/Users/17536/.workbuddy/binaries/node/workspace/node_modules/playwright-core/index.mjs'

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const BASE = 'http://127.0.0.1:5174/Lun-Assistant/console/tuner.html'
const OUT = 'D:\\PythonProject\\Lun-Assistant\\frontend\\_theme-shots'

const THEMES = [
  { id: 'a', name: 'A-柔雾青绿' },
  { id: 'b', name: 'B-水墨留白' },
  { id: 'c', name: 'C-暗墨夜山' },
  { id: 'd', name: 'D-青绿金碧' },
]

const browser = await chromium.launch({
  executablePath: CHROME,
  args: ['--no-proxy-server', '--disable-gpu'],
})
const page = await browser.newPage({ viewport: { width: 1680, height: 1000 } })

const errors = []
page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`))
page.on('console', (m) => { if (m.type() === 'error') errors.push(`console: ${m.text()}`) })

await page.goto(BASE, { waitUntil: 'networkidle' })
await page.waitForTimeout(1200)

// 读取页面里实际渲染出的主题 tab（验证数量与命名）
const tabs = await page.$$eval('.theme-tabs button', (els) =>
  els.map((el) => ({ theme: el.dataset.theme, label: el.textContent.trim().replace(/\s+/g, ' ') }))
)
console.log('主题 tab 数量:', tabs.length)
console.log(JSON.stringify(tabs, null, 2))

// 确认 D 背景图真实可加载（不是 404）
const bgOk = await page.evaluate(async () => {
  const r = await fetch('../bg/bg-d-jinbi.webp', { method: 'GET' })
  return { status: r.status, ok: r.ok }
})
console.log('D 背景图请求:', JSON.stringify(bgOk))

for (const t of THEMES) {
  await page.click(`.theme-tabs button[data-theme="${t.id}"]`)
  await page.waitForTimeout(900) // 等主题过渡动画结束

  // 抓当前生效的关键样式，便于核对
  const probe = await page.evaluate(() => {
    const stage = document.querySelector('.stage')
    const photo = document.querySelector('.ink-photo')
    const cs = getComputedStyle(stage)
    const ps = getComputedStyle(photo)
    return {
      themeAttr: document.body.dataset.theme,
      stageBg: cs.backgroundColor,
      photoImage: ps.backgroundImage.slice(0, 90),
      photoOpacity: ps.opacity,
      verTag: document.getElementById('verTag')?.textContent,
    }
  })
  console.log(`\n[${t.name}]`, JSON.stringify(probe, null, 2))

  const file = `${OUT}\\${t.name}.png`
  await page.screenshot({ path: file })
  console.log('  截图 ->', file)
}

if (errors.length) {
  console.log('\n页面错误:')
  errors.forEach((e) => console.log('  ', e))
} else {
  console.log('\n无页面错误')
}

await browser.close()
