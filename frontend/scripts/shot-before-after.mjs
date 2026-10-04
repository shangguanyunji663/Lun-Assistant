/* 修复前 / 修复后 对照截图
   修复前：临时把 layout.css 的外壳锁定规则摘掉（还原 8 份皮肤各自 min-height:100vh 的行为），
           模拟用户报的现象「消息区无限撑高、输入框被顶走」。
   运行时会真实改文件再还原，故只在本地验证用，不入库。 */
import { chromium } from 'file:///C:/Users/17536/.workbuddy/binaries/node/workspace/node_modules/playwright-core/index.mjs'
import { readFileSync, writeFileSync } from 'node:fs'

const LAYOUT = 'src/styles/layout.css'
const OUT = 'D:\\PythonProject\\Lun-Assistant\\frontend\\_verify-shots'
const orig = readFileSync(LAYOUT, 'utf-8')

// 关闭修复：把外壳锁定相关的 4 条规则注释掉
const DISABLED = orig
  .replace(/html\[data-skin\] \.wb \{\n  height: 100vh;/, '/*OFF*/ html[data-skin] .wb {\n  /* height: 100vh;')
  .replace(/^  height: 100dvh;$/m, '  /* height: 100dvh; */')
  .replace(/^  min-height: 0;$/m, '  /* min-height: 0; */')
  .replace(/^  overflow: hidden;$/m, '  /* overflow: hidden; */')

if (DISABLED === orig) { console.error('!! 未能定位 layout.css 中的锁定规则'); process.exit(1) }

const browser = await chromium.launch({
  executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  args: ['--no-proxy-server', '--disable-gpu'],
})

const seed = () => {
  const msgs = []
  for (let i = 0; i < 14; i++) {
    msgs.push({ role: 'user', content: `第 ${i + 1} 轮：帮我梳理第三章方法论，需要实验设计与信效度检验。`, ts: Date.now() - (14 - i) * 60000 })
    msgs.push({ role: 'assistant', content: `第 ${i + 1} 轮回答。\n\n## 建议\n\n1. **实验设计**：明确自变量、因变量与控制变量，给出对照组划分依据。\n2. **信效度**：内容效度用专家评议，结构效度用因子分析，信度用 Cronbach's α ≥ 0.7。\n3. **数据来源**：说明抽样框、样本量与剔除规则。\n\n> 结论先行：先锁定研究问题，再倒推指标体系。`, ts: Date.now() - (14 - i) * 60000 + 800 })
  }
  return JSON.stringify([
    { id: 'web-a', title: '大模型辅助的文献综述', updatedAt: Date.now(), interrupt: null, timeline: [], msgs },
    { id: 'web-b', title: '古籍校勘方向选题', updatedAt: Date.now() - 60000, interrupt: null, timeline: [], msgs: [{ role: 'user', content: '另一个会话', ts: Date.now() }] },
  ])
}

async function shoot(tag) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  await page.route('**/api/auth/me', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, username: '国伟', role: 'admin' }) }))
  await page.route('**/api/projects', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }))
  await page.addInitScript((s) => { localStorage.setItem('lj_token', 'mock'); localStorage.setItem('lj_sessions_v1', s) }, seed())
  await page.goto('http://127.0.0.1:5173/app.html', { waitUntil: 'networkidle' })
  await page.waitForSelector('.wb-stream')
  await page.waitForTimeout(2000)
  const m = await page.evaluate(() => {
    const de = document.documentElement
    const st = document.querySelector('.wb-stream')
    const cp = document.querySelector('.wb-compose')
    return {
      页面可滚动像素: de.scrollHeight - de.clientHeight,
      消息区高: st.clientHeight,
      消息区内容高: st.scrollHeight,
      消息区自身可滚: st.scrollHeight - st.clientHeight,
      输入框底边: Math.round(cp.getBoundingClientRect().bottom),
      视口高: window.innerHeight,
      输入框在屏内: cp.getBoundingClientRect().bottom <= window.innerHeight + 1,
    }
  })
  await page.screenshot({ path: `${OUT}\\${tag}.png` })
  await page.close()
  return m
}

try {
  writeFileSync(LAYOUT, DISABLED)
  await new Promise((r) => setTimeout(r, 1200))
  const before = await shoot('BEFORE-修复前')

  writeFileSync(LAYOUT, orig)
  await new Promise((r) => setTimeout(r, 1200))
  const after = await shoot('AFTER-修复后')

  const row = (k) => console.log(`  ${k.padEnd(14)} 修复前 ${String(before[k]).padStart(6)}   修复后 ${String(after[k]).padStart(6)}`)
  console.log('\n  指标              修复前        修复后')
  console.log('  ' + '-'.repeat(46))
  row('页面可滚动像素')
  row('消息区高')
  row('消息区内容高')
  row('消息区自身可滚')
  row('输入框底边')
  row('输入框在屏内')
  console.log(`\n  截图: _verify-shots/BEFORE-修复前.png / AFTER-修复后.png`)
} finally {
  writeFileSync(LAYOUT, orig)
  console.log('\n  已还原 layout.css')
  await browser.close()
}
