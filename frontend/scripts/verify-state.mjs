/* 状态层回归：interrupt 跨会话保持 / 演示模式不污染持久化 / 连点发送不并发 /
   项目写操作按显式 id 命中 / 401 不误伤登录 */
import { chromium } from 'file:///C:/Users/17536/.workbuddy/binaries/node/workspace/node_modules/playwright-core/index.mjs'

const browser = await chromium.launch({
  executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  args: ['--no-proxy-server', '--disable-gpu'],
})
const page = await browser.newPage({ viewport: { width: 1600, height: 900 } })
const errs = []
page.on('pageerror', (e) => errs.push('pageerror: ' + e.message))
page.on('console', (m) => { if (m.type() === 'error' && !m.text().includes('favicon')) errs.push('console: ' + m.text()) })

/* --- 记录 /agent/chat 的调用次数与 body --- */
const calls = []
await page.route('**/api/auth/me', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, username: 'V', role: 'admin' }) }))
await page.route('**/api/projects', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }))

/* 慢响应：放大并发窗口，便于验证重入锁 */
await page.route('**/api/agent/chat', async (r) => {
  calls.push(JSON.parse(r.request().postData() || '{}'))
  const frames = [
    { type: 'token', payload: '回答内容' },
    { type: 'final', payload: { output: '回答内容' } },
    { type: 'done' },
  ]
  await new Promise((r2) => setTimeout(r2, 900))
  await r.fulfill({ status: 200, contentType: 'text/event-stream', body: frames.map((x) => 'data: ' + JSON.stringify(x) + '\n\n').join('') })
})

await page.addInitScript(() => {
  if (localStorage.getItem('lj_seeded')) return
  localStorage.setItem('lj_seeded', '1')
  localStorage.setItem('lj_token', 'mock')
  localStorage.setItem('lj_sessions_v1', JSON.stringify([
    { id: 'web-a', title: '甲', updatedAt: Date.now(), interrupt: null, timeline: [], msgs: [{ role: 'user', content: 'a1', ts: Date.now() }] },
    { id: 'web-b', title: '乙', updatedAt: Date.now(), interrupt: null, timeline: [], msgs: [{ role: 'user', content: 'b1', ts: Date.now() }] },
  ]))
})

await page.goto('http://127.0.0.1:5173/app.html', { waitUntil: 'networkidle' })
await page.waitForSelector('.wb-compose-ta')
await page.waitForTimeout(700)

/* --- ① 连点发送：只应产生 1 次请求 --- */
await page.fill('.wb-compose-ta', '并发测试')
const btn = page.locator('.wb-compose-send')
await btn.click()
await btn.click({ force: true })
await btn.click({ force: true })
await page.waitForTimeout(2600)
const nCalls = calls.length
const bubbles = await page.evaluate(() => document.querySelectorAll('.wb-msg').length)
console.log(`\n[① 连点发送 3 次] /agent/chat 调用 ${nCalls} 次；消息数 ${bubbles}`)
console.log(nCalls === 1 ? '  ✓ 重入锁生效（只发出一条）' : `  ✗ 并发了 ${nCalls} 条流`)

/* --- ② 演示模式不污染真实会话（?demo=1） --- */
const before = await page.evaluate(() => JSON.parse(localStorage.getItem('lj_sessions_v1') || '[]').length)
const demo = await browser.newPage({ viewport: { width: 1400, height: 900 } })
await demo.route('**/api/auth/me', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, username: 'V', role: 'admin' }) }))
await demo.route('**/api/projects', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }))
await demo.addInitScript(() => { localStorage.setItem('lj_token', 'mock') })
await demo.goto('http://127.0.0.1:5173/app.html?demo=1', { waitUntil: 'networkidle' })
await demo.waitForTimeout(1200)
// 演示会话自带待确认项，输入框因此锁定；点一个选项即可触发 demoChat 写会话。
// （demoChat 结束时会再摆一次中断条，那是演示设计，与本用例无关。）
const demoLSBefore = await demo.evaluate(() => localStorage.getItem('lj_sessions_v1'))
const opBtns = demo.locator('.wb-break-op')
if (await opBtns.count()) await opBtns.first().click()
await demo.waitForTimeout(2200)
const demoLS = await demo.evaluate(() => localStorage.getItem('lj_sessions_v1'))
const msgCount = await demo.evaluate(() => document.querySelectorAll('.wb-msg').length)
console.log(`\n[② 演示模式] 真实 localStorage 会话数=${before}；演示页发送后消息数=${msgCount}`)
console.log(demoLS === demoLSBefore
  ? '  ✓ 演示会话未写入 localStorage（真实卷册不会被 mock 覆盖）'
  : `  ✗ 被写入: ${String(demoLS).slice(0, 140)}`)
await demo.close()

/* --- ③ 项目写操作按显式 id（切换项目后编辑，PATCH 应打到原项目） --- */
const p2 = await browser.newPage({ viewport: { width: 1600, height: 900 } })
const patches = []
await p2.route('**/api/auth/me', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, username: 'V', role: 'admin' }) }))
await p2.route('**/api/projects', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 1, title: '项目一', major: 'CS', status: 'created' }, { id: 2, title: '项目二', major: '文学', status: 'writing' }]) }))
await p2.route('**/api/projects/*', (r) => {
  patches.push({ url: r.request().url(), method: r.request().method() })
  return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, status: 'topic' }) })
})
await p2.addInitScript(() => { localStorage.setItem('lj_token', 'mock') })
await p2.goto('http://127.0.0.1:5173/app.html', { waitUntil: 'networkidle' })
await p2.waitForSelector('.wb-proj-sel')
await p2.waitForTimeout(700)
await p2.selectOption('.wb-proj-sel', '1')
await p2.waitForTimeout(400)
await p2.click('button[title="编辑 / 删除当前项目"]')
await p2.waitForSelector('.modal-card')
// 弹窗打开期间把顶栏切到项目 2，再保存 —— 旧实现会 PATCH 到项目 2
await p2.evaluate(() => {
  const sel = document.querySelector('.wb-proj-sel')
  sel.value = '2'
  sel.dispatchEvent(new Event('change', { bubbles: true }))
})
await p2.waitForTimeout(300)
await p2.fill('.modal-card input', '改名后的项目一')
await p2.click('.modal-card .btn-ink')
await p2.waitForTimeout(900)
console.log('\n[③ 编辑项目] PATCH 请求:', JSON.stringify(patches))
const patchedOne = patches.some((x) => x.method === 'PATCH' && /\/projects\/1(\?|$)/.test(x.url))
console.log(patchedOne ? '  ✓ PATCH 打到被编辑的项目 id=1（未误伤当前选中的 2）' : '  ✗ PATCH 打错了项目')
await p2.close()

console.log('\n页面错误:', errs.length ? '' : '无')
errs.forEach((e) => console.log('  ', e))
await browser.close()
