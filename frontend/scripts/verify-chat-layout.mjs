/* 对话区固定高度 + 粘底滚动 验证脚本（真实驱动 UI，mock API）
   断言：
     1) 注入大量消息后，页面本身不滚（documentElement.scrollHeight <= innerHeight）
     2) .wb-stream 是唯一滚动容器（scrollHeight > clientHeight 且可独立滚动）
     3) 输入框固定在底部且始终可见
     4) 上翻历史时出现「回到底部」按钮，且不自动拽回底部
     5) 点按钮回到底部
     6) 切换会话后自动回到底部
*/
import { chromium } from 'file:///C:/Users/17536/.workbuddy/binaries/node/workspace/node_modules/playwright-core/index.mjs'

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const BASE = 'http://127.0.0.1:5173/app.html'
const OUT = 'D:\\PythonProject\\Lun-Assistant\\frontend\\_verify-shots'

const browser = await chromium.launch({ executablePath: CHROME, args: ['--no-proxy-server', '--disable-gpu'] })
const page = await browser.newPage({ viewport: { width: 1600, height: 900 } })

const errors = []
page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`))
page.on('console', (m) => { if (m.type() === 'error' && !m.text().includes('favicon')) errors.push(`console: ${m.text()}`) })

await page.route('**/api/auth/me', (r) => r.fulfill({
  status: 200, contentType: 'application/json',
  body: JSON.stringify({ id: 1, username: '验证用户', role: 'admin' }),
}))
await page.route('**/api/projects', (r) => r.fulfill({
  status: 200, contentType: 'application/json', body: '[]',
}))

// 预置 3 个会话，每会话 12 轮对话，制造远超视口的内容量
await page.addInitScript(() => {
  try {
    localStorage.setItem('lj_token', 'mock-token')
    const mk = (n, tag) => ({
      id: `web-verify-${n}`,
      title: `${tag}会话`,
      updatedAt: Date.now() - n * 60000,
      interrupt: null,
      timeline: [{ type: 'intent', payload: { label: '论文选题', layer: 'rule', confidence: 0.9 } }],
      msgs: Array.from({ length: 12 }, (_, i) => ([
        { role: 'user', content: `【${tag}】第 ${i + 1} 轮提问：帮我梳理一下第三章的方法论部分，需要补充实验设计与信效度检验，请给出可执行的写作建议。`, ts: Date.now() - (12 - i) * 60000 },
        { role: 'assistant', content: `【${tag}】第 ${i + 1} 轮回答。\n\n## 建议\n\n1. **实验设计**：明确自变量、因变量与控制变量，给出对照组与实验组的划分依据。\n2. **信效度**：内容效度用专家评议，结构效度用因子分析，信度用 Cronbach's α ≥ 0.7。\n3. **数据来源**：说明抽样框、样本量与剔除规则，保证可复现。\n\n> 结论先行：先锁定研究问题，再倒推指标体系。`, ts: Date.now() - (12 - i) * 60000 + 1000 },
      ])).flat(),
    })
    localStorage.setItem('lj_sessions_v1', JSON.stringify([mk(1, '甲'), mk(2, '乙'), mk(3, '丙')]))
  } catch (e) {}
})

await page.goto(BASE, { waitUntil: 'networkidle' })
await page.waitForSelector('.wb-stream', { timeout: 20000 })
await page.waitForTimeout(900)

const R = []
const probe = async (label) => {
  const m = await page.evaluate(() => {
    const de = document.documentElement
    const stream = document.querySelector('.wb-stream')
    const compose = document.querySelector('.wb-compose')
    const wb = document.querySelector('.wb')
    const jump = document.querySelector('.wb-jump')
    const sr = stream.getBoundingClientRect()
    const cr = compose.getBoundingClientRect()
    return {
      pageScrollable: de.scrollHeight - de.clientHeight,
      wbH: Math.round(wb.getBoundingClientRect().height),
      viewportH: window.innerHeight,
      streamScrollH: stream.scrollHeight,
      streamClientH: stream.clientHeight,
      streamScrollTop: Math.round(stream.scrollTop),
      streamScrollable: stream.scrollHeight - stream.clientHeight,
      atBottomPx: Math.round(stream.scrollHeight - stream.scrollTop - stream.clientHeight),
      composeBottom: Math.round(cr.bottom),
      composeVisible: cr.top < window.innerHeight && cr.bottom <= window.innerHeight + 1,
      streamBottom: Math.round(sr.bottom),
      jumpVisible: !!jump,
    }
  })
  R.push([label, m])
  return m
}

const a = await probe('① 初始（首屏）')
console.log('\n[① 初始]', JSON.stringify(a, null, 1))

// 断言 1：页面本身不滚
console.log(a.pageScrollable <= 1 ? '  ✓ 页面不滚动（固定窗口）' : `  ✗ 页面仍可滚 ${a.pageScrollable}px`)
console.log(a.composeVisible ? '  ✓ 输入框固定在底部且可见' : '  ✗ 输入框不在视口内')
console.log(a.atBottomPx <= 64 ? '  ✓ 首屏已贴底' : `  ✗ 首屏未贴底（距底 ${a.atBottomPx}px）`)

// 断言 2：消息区独立滚动
console.log(a.streamScrollable > 100 ? `  ✓ 消息区独立滚动（可滚 ${a.streamScrollable}px）` : '  ✗ 消息区没有溢出')
await page.screenshot({ path: `${OUT}\\1-首屏贴底.png` })

// 断言 3：上翻历史 → 出现回到底部按钮，且不被拽回
await page.evaluate(() => { document.querySelector('.wb-stream').scrollTop = 0 })
await page.waitForTimeout(600)
const b = await probe('② 上翻到顶')
console.log('\n[② 上翻到顶]', JSON.stringify(b, null, 1))
console.log(b.jumpVisible ? '  ✓ 出现「回到底部」按钮' : '  ✗ 未出现回到底部按钮')
console.log(b.streamScrollTop < 50 ? '  ✓ 未被自动拽回底部（可翻阅历史）' : `  ✗ 被拽回了 ${b.streamScrollTop}px`)
await page.screenshot({ path: `${OUT}\\2-上翻历史.png` })

// 断言 4：点按钮回到底部
await page.click('.wb-jump')
await page.waitForTimeout(2500)
await page.waitForTimeout(900)
const c = await probe('③ 点回到底部')
console.log('\n[③ 点回到底部]', JSON.stringify(c, null, 1))
console.log(c.atBottomPx <= 64 ? '  ✓ 已回到底部' : `  ✗ 未回到底部（距底 ${c.atBottomPx}px）`)
console.log(!c.jumpVisible ? '  ✓ 按钮已隐藏' : '  ✗ 按钮仍在')
await page.screenshot({ path: `${OUT}\\3-回到底部.png` })

// 断言 5：切换会话后自动回到底部
await page.evaluate(() => { document.querySelector('.wb-stream').scrollTop = 0 })
await page.waitForTimeout(400)
const vols = page.locator('.wb-vol')
await vols.nth(1).click()
await page.waitForTimeout(900)
const d = await probe('④ 切换会话后')
console.log('\n[④ 切换会话]', JSON.stringify(d, null, 1))
console.log(d.atBottomPx <= 64 ? '  ✓ 新会话自动回到底部' : `  ✗ 停在 ${d.atBottomPx}px 处`)

// 断言 6：发一条消息后仍贴底
await page.fill('.wb-compose-ta', '帮我再补充一段关于研究伦理的说明')
await page.waitForTimeout(200)
await page.click('.wb-compose-send')
await page.waitForTimeout(2600)
const e2 = await probe('⑤ 发送后')
console.log('\n[⑤ 发送后]', JSON.stringify(e2, null, 1))
console.log(e2.atBottomPx <= 80 ? '  ✓ 新消息后自动滚到底' : `  ✗ 未跟随（距底 ${e2.atBottomPx}px）`)
await page.screenshot({ path: `${OUT}\\4-发送后.png` })

// 六套皮肤各验一次布局（防止只修好 A）
console.log('\n[六套皮肤布局体检]')
for (const sk of ['a', 'b', 'c', 'd', 'e', 'f']) {
  await page.evaluate((s) => { localStorage.setItem('lj_skin', s); document.documentElement.dataset.skin = s }, sk)
  await page.waitForTimeout(450)
  const mm = await page.evaluate(() => {
    const de = document.documentElement
    const st = document.querySelector('.wb-stream')
    const cp = document.querySelector('.wb-compose')
    return {
      pageScroll: de.scrollHeight - de.clientHeight,
      streamOverflow: st.scrollHeight - st.clientHeight,
      composeInView: cp.getBoundingClientRect().bottom <= window.innerHeight + 1,
    }
  })
  const ok = mm.pageScroll <= 1 && mm.composeInView
  console.log(`  ${ok ? '✓' : '✗'} 皮肤 ${sk}: 页面滚动=${mm.pageScroll}px 消息区可滚=${mm.streamOverflow}px 输入框在视口=${mm.composeInView}`)
  await page.screenshot({ path: `${OUT}\\skin-${sk}.png` })
}

console.log('\n页面错误:', errors.length ? '' : '无')
errors.forEach((e) => console.log('  ', e))
await browser.close()
