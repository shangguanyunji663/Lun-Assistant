/* 多视口回归：确认各断点下输入框可达、页面不被裁切、消息区独立滚动 */
import { chromium } from 'file:///C:/Users/17536/.workbuddy/binaries/node/workspace/node_modules/playwright-core/index.mjs'

const browser = await chromium.launch({
  executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  args: ['--no-proxy-server', '--disable-gpu'],
})
const SIZES = [[1920, 1080], [1440, 900], [1280, 800], [1024, 768], [900, 700], [820, 900], [768, 1024], [430, 860], [390, 844], [360, 640]]

for (const [w, h] of SIZES) {
  const p = await browser.newPage({ viewport: { width: w, height: h } })
  await p.route('**/api/auth/me', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, username: 'V', role: 'admin' }) }))
  await p.route('**/api/projects', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }))
  await p.addInitScript(() => {
    localStorage.setItem('lj_token', 'm')
    const msgs = []
    for (let i = 0; i < 10; i++) {
      msgs.push({ role: 'user', content: `第 ${i + 1} 轮提问`, ts: Date.now() })
      msgs.push({ role: 'assistant', content: `第 ${i + 1} 轮回答`, ts: Date.now() })
    }
    localStorage.setItem('lj_sessions_v1', JSON.stringify([
      { id: 'w', title: 'T', updatedAt: Date.now(), interrupt: null, timeline: [], msgs },
    ]))
  })
  await p.goto('http://127.0.0.1:5173/app.html', { waitUntil: 'networkidle' })
  await p.waitForTimeout(1400)
  const m = await p.evaluate(() => {
    const de = document.documentElement
    const cp = document.querySelector('.wb-compose')
    const st = document.querySelector('.wb-stream')
    return {
      pageScroll: de.scrollHeight - de.clientHeight,
      composeInView: cp.getBoundingClientRect().bottom <= window.innerHeight + 1,
      streamH: st.clientHeight,
      streamOverflow: st.scrollHeight - st.clientHeight,
      wbH: Math.round(document.querySelector('.wb').getBoundingClientRect().height),
    }
  })
  const mark = m.composeInView ? 'OK ' : 'NG '
  console.log(`  [${mark}] ${String(w).padStart(4)}x${String(h).padEnd(4)} wbH=${String(m.wbH).padStart(5)} pageScroll=${String(m.pageScroll).padStart(5)} stream=${String(m.streamH).padStart(4)}(overflow ${m.streamOverflow}) composeVisible=${m.composeInView}`)
  await p.close()
}
await browser.close()
