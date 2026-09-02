/* 上传三态文案验证 v2：mock 后端接口，验证「重复上传→去重跳过」与「部分新入库」文案。 */
import { chromium } from 'file:///C:/Users/17536/.workbuddy/binaries/node/workspace/node_modules/playwright-core/index.mjs'

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
const OUT = 'D:\\PythonProject\\Lun-Assistant\\frontend\\_verify-upload'
const dupTxt = 'D:\\PythonProject\\Lun-Assistant\\frontend\\_verify-upload\\dup-sample.txt'
const newTxt = 'D:\\PythonProject\\Lun-Assistant\\frontend\\_verify-upload\\new-doc.txt'

const browser = await chromium.launch({ executablePath: CHROME, args: ['--no-proxy-server'] })
const page = await browser.newPage({ viewport: { width: 1600, height: 900 } })

// ---- 基础 mock ----
await page.route('**/api/auth/me', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, username: 'u', role: 'admin' }) }))
await page.route('**/api/projects', (r) => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 1, title: 'P1', major: 'x', requirement: '' }]) }))

// 知识库：GET → 库中已有 ready 文档；POST → 由变量控制返回（先 0 ready 全 skipped）
let uploadResp = null
await page.route('**/knowledge**', (r) => {
  const m = r.request().method()
  if (m === 'GET') {
    return r.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ project_id: 1, count: 1, documents: [{ id: 1, filename: '示例论文1.docx', file_type: 'docx', size_bytes: 1, status: 'ready', chunk_count: 14, word_count: 4674, error: null }] }) })
  }
  if (m === 'POST' && uploadResp) {
    return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(uploadResp) })
  }
  return r.continue()
})

await page.addInitScript(() => { try { localStorage.setItem('lj_token', 't'); localStorage.setItem('lj_theme', 'a') } catch {} })
await page.goto('http://localhost:5173/', { waitUntil: 'networkidle' })
await page.waitForSelector('.proj-picker select', { timeout: 20000 })
await page.selectOption('.proj-picker select', '1')
await page.locator('.side-tabs button', { hasText: '项目知识库' }).click()
await page.waitForSelector('.kb-drop input[type=file]', { state: 'attached', timeout: 10000 })

// 场景 1：重复上传 → 0 ready + 1 skipped
uploadResp = { project_id: 1, uploaded: 1, ready: 0,
  results: [{ status: 'skipped', filename: '示例论文1.docx', id: 1, reason: '同项目已存在相同内容文件' }] }
await page.locator('.kb-drop input[type=file]').setInputFiles(dupTxt)
await page.waitForTimeout(1200)
const msg1 = (await page.locator('.kb-upload-msg').innerText()).replace(/\s+/g, ' ').trim()
console.log('场景1(全部去重) →', JSON.stringify(msg1))
await page.screenshot({ path: `${OUT}\\S1-去重跳过.png` })

// 场景 2：1 新 + 1 重复
uploadResp = { project_id: 1, uploaded: 2, ready: 1,
  results: [
    { status: 'ready', filename: '新文档-方法论.docx', id: 9 },
    { status: 'skipped', filename: '示例论文1.docx', id: 1, reason: '同项目已存在相同内容文件' },
  ] }
await page.locator('.kb-drop input[type=file]').setInputFiles([newTxt, dupTxt])
await page.waitForTimeout(1200)
const msg2 = (await page.locator('.kb-upload-msg').innerText()).replace(/\s+/g, ' ').trim()
console.log('场景2(1新+1重) →', JSON.stringify(msg2))
await page.screenshot({ path: `${OUT}\\S2-部分入库.png` })

// 场景 3：解析失败
uploadResp = { project_id: 1, uploaded: 1, ready: 0,
  results: [{ status: 'failed', filename: '坏文件.pdf', id: null, error: '解析失败: 无法读取内容' }] }
await page.locator('.kb-drop input[type=file]').setInputFiles(newTxt)
await page.waitForTimeout(1200)
const msg3 = (await page.locator('.kb-upload-msg').innerText()).replace(/\s+/g, ' ').trim()
console.log('场景3(解析失败) →', JSON.stringify(msg3))
await page.screenshot({ path: `${OUT}\\S3-解析失败.png` })

await browser.close()
console.log('\n验证完成')
