/* 中断（人机介入）跨会话保持 + 移动端布局 验证 */
import { chromium } from 'file:///C:/Users/17536/.workbuddy/binaries/node/workspace/node_modules/playwright-core/index.mjs'
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const BASE = 'http://127.0.0.1:5173/app.html'
const OUT = 'D:\\PythonProject\\Lun-Assistant\\frontend\\_verify-shots'

const browser = await chromium.launch({ executablePath: CHROME, args: ['--no-proxy-server', '--disable-gpu'] })

/* ---------- 1. interrupt 跨会话保持 ---------- */
const page = await browser.newPage({ viewport: { width: 1600, height: 900 } })
const errs = []
page.on('pageerror', (e) => errs.push('pageerror: ' + e.message))
page.on('console', (m) => { if (m.type() === 'error' && !m.text().includes('favicon')) errs.push('console: ' + m.text()) })

await page.route('**/api/auth/me', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, username: 'V', role: 'admin' }) }))
await page.route('**/api/projects', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }))

// SSE：先 token 若干，再发 interrupt，然后结束
await page.route('**/api/agent/chat', async (r) => {
  const frames = [
    { type: 'intent', payload: { label: '选题', layer: 'rule', confidence: 0.93 } },
    { type: 'node_start', payload: { agent: 'topic_agent', title: '选题助手' }, node: 'topic_agent' },
    { type: 'token', payload: '我为你拟了三个选题方向：' },
    { type: 'token', payload: '\n\n1. **古籍校勘的大模型辅助**\n2. **文献综述自动化**\n3. **引用规范校验**\n\n' },
    { type: 'interrupt', payload: { type: 'confirm', agent: 'topic_agent', question: '请确认选题方案，或提出调整意见', proposal: '建议方向 1：古籍校勘的大模型辅助（数据可得、评测清晰）', options: ['采纳该方案', '调整为方向 2', '重新生成'] }, node: 'topic_agent' },
    { type: 'done' },
  ]
  await r.fulfill({ status: 200, contentType: 'text/event-stream', body: frames.map((f) => `data: ${JSON.stringify(f)}\n\n`).join('') })
})

await page.addInitScript(() => {
  localStorage.setItem('lj_token', 'mock')
  // 哨兵：addInitScript 每次导航都会执行，若无此判断，reload 会把
  // 上一步刚持久化的会话（含 interrupt）重新覆盖成初始值 —— 那是测试自身
  // 的问题，不是产品缺陷。
  if (localStorage.getItem('lj_seeded')) return
  localStorage.setItem('lj_seeded', '1')
  localStorage.setItem('lj_sessions_v1', JSON.stringify([
    { id: 'web-a', title: '甲会话', updatedAt: Date.now(), interrupt: null, timeline: [], msgs: [{ role: 'user', content: '第一句', ts: Date.now() }] },
    { id: 'web-b', title: '乙会话', updatedAt: Date.now(), interrupt: null, timeline: [], msgs: [{ role: 'user', content: '乙的第一句', ts: Date.now() }] },
  ]))
})

await page.goto(BASE, { waitUntil: 'networkidle' })
await page.waitForSelector('.wb-compose-ta')
await page.waitForTimeout(800)

await page.fill('.wb-compose-ta', '帮我确定一个可行的论文选题')
await page.click('.wb-compose-send')
await page.waitForSelector('.wb-break', { timeout: 15000 })
await page.waitForTimeout(1200)

const s1 = await page.evaluate(() => ({
  barVisible: !!document.querySelector('.wb-break'),
  options: [...document.querySelectorAll('.wb-break-op')].map((e) => e.textContent.trim()),
  lastBubble: document.querySelector('.wb-msg:last-of-type .wb-bubble')?.innerText.slice(0, 60),
  emptyInputDisabled: document.querySelector('.wb-compose-ta').disabled,
}))
console.log('\n[① interrupt 到达]', JSON.stringify(s1, null, 1))
console.log(s1.barVisible ? '  ✓ 中断确认条出现' : '  ✗ 确认条未出现')
console.log(s1.options.length ? `  ✓ 选项渲染: ${s1.options.join(' / ')}` : '  ✗ 选项为空')
console.log(s1.lastBubble && !/等待|取消|没有产出/.test(s1.lastBubble) ? '  ✓ 助手气泡非空' : '  ✗ 助手气泡留空')
console.log(s1.emptyInputDisabled ? '  ✓ 确认期间主输入框锁定' : '  ✗ 主输入框未锁定')
await page.screenshot({ path: `${OUT}\\interrupt-1-到达.png` })

// 切到乙会话 → 再切回甲
await page.locator('.wb-vol').nth(1).click()
await page.waitForTimeout(700)
const s2 = await page.evaluate(() => ({ barVisible: !!document.querySelector('.wb-break') }))
console.log(`\n[② 切到乙会话] 确认条可见=${s2.barVisible} ${s2.barVisible ? '✗ 应已隐藏' : '✓ 已隐藏'}`)

await page.locator('.wb-vol').nth(0).click()
await page.waitForTimeout(700)
const s3 = await page.evaluate(() => ({
  barVisible: !!document.querySelector('.wb-break'),
  question: document.querySelector('.wb-break-ask')?.innerText,
  lastBubble: document.querySelector('.wb-msg:last-of-type .wb-bubble')?.innerText.slice(0, 40),
}))
console.log('[③ 切回甲会话]', JSON.stringify(s3, null, 1))
console.log(s3.barVisible ? '  ✓ 切回后待确认项仍在（不再丢失）' : '  ✗ 切回后待确认项丢失')
await page.screenshot({ path: `${OUT}\\interrupt-2-切回.png` })

// 刷新页面：待确认项应从 localStorage 恢复
await page.reload({ waitUntil: 'networkidle' })
await page.waitForTimeout(1200)
const s4 = await page.evaluate(() => ({ barVisible: !!document.querySelector('.wb-break') }))
console.log(`[④ 刷新页面] 确认条可见=${s4.barVisible} ${s4.barVisible ? '✓ 持久化恢复' : '✗ 刷新后丢失'}`)

await page.close()

/* ---------- 2. 移动端窄屏：应退化为整页滚动且不被裁切 ---------- */
const m = await browser.newPage({ viewport: { width: 430, height: 860 }, isMobile: true, hasTouch: true })
await m.route('**/api/auth/me', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, username: 'V', role: 'admin' }) }))
await m.route('**/api/projects', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }))
await m.addInitScript(() => {
  localStorage.setItem('lj_token', 'mock')
  const msgs = []
  for (let i = 0; i < 10; i++) {
    msgs.push({ role: 'user', content: `第 ${i + 1} 轮：帮我补充第三章方法论。`, ts: Date.now() })
    msgs.push({ role: 'assistant', content: `第 ${i + 1} 轮回答：\n\n1. **实验设计**：明确变量。\n2. **信效度**：专家评议 + 因子分析。`, ts: Date.now() })
  }
  localStorage.setItem('lj_sessions_v1', JSON.stringify([{ id: 'web-m', title: '移动端', updatedAt: Date.now(), interrupt: null, timeline: [], msgs }]))
})
await m.goto(BASE, { waitUntil: 'networkidle' })
await m.waitForSelector('.wb-stream')
await m.waitForTimeout(1500)
const mm = await m.evaluate(() => {
  const de = document.documentElement
  const wb = document.querySelector('.wb')
  const st = document.querySelector('.wb-stream')
  const cp = document.querySelector('.wb-compose')
  return {
    pageScrollable: de.scrollHeight - de.clientHeight,
    wbOverflow: getComputedStyle(wb).overflow,
    streamOverflow: st.scrollHeight - st.clientHeight,
    streamClientH: st.clientHeight,
    composeInView: cp.getBoundingClientRect().bottom <= window.innerHeight + 1,
  }
})
console.log('\n[⑤ 移动端 430px]', JSON.stringify(mm, null, 1))
console.log(mm.wbOverflow === 'visible' ? '  ✓ 窄屏退化为整页滚动（未被裁切）' : `  ✗ overflow=${mm.wbOverflow}`)
console.log(mm.pageScrollable > 0 ? '  ✓ 页面可滚到底（内容未被截断）' : '  ✗ 页面无法滚动，内容可能不可达')
console.log(mm.composeInView ? '  ✓ 输入框在视口内' : '  ✗ 输入框不可见')
await m.screenshot({ path: `${OUT}\\mobile-430.png`, fullPage: false })

console.log('\n页面错误:', errs.length ? '' : '无')
errs.forEach((e) => console.log('  ', e))
await browser.close()
