/* ============================================================================
   v18 · 落地页共享行为
   —— 六张落地页（index.html + landing-b…f.html）各自导入本模块，
      拿到完全一致的四件事，避免 6 份重复实现：

        1. 皮肤同步   ：把本页皮肤写进 localStorage.lj_skin，工作台跟随
        2. 皮肤切换器 ：注入左下角 .sw（六套设计语言互跳）
        3. 入场编排   ：[data-reveal] 进视口揭示 / [data-count] 数字滚动 /
                        [data-typewriter] 逐字打字
        4. 彩蛋机关   ：三门手势（手速 / 精读 / 书写），含「落笔处」砚纸

   所有节点都用 DOM 注入，页面本身只需：
     <html data-skin="X">
     <link rel="stylesheet" href="/src/landing/shared.css">
     <script type="module" src="/src/landing/shared.js"></script>
   ============================================================================ */

import { SKINS, findSkin, loadSkin, saveSkin } from '../skins/registry.js'
import { initPointerFx, toast } from '../fx.js'

const PAGE_SKIN = findSkin(document.documentElement.dataset.skin || 'a').id
const REDUCE = window.matchMedia
  ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
  : false

/* 本页皮肤优先：用户经由本页进入工作台时，工作台应与本页一致 */
saveSkin(PAGE_SKIN)

/* ============================================================ 1. 皮肤切换器 */
function mountSkinSwitcher() {
  const cur = findSkin(PAGE_SKIN)

  const box = document.createElement('div')
  box.className = 'sw'
  box.innerHTML = `
    <button class="sw-trigger" type="button" aria-haspopup="true" aria-expanded="false">
      <span class="sw-dot" style="--sw-c:${cur.chip}"></span>
      <span>切换皮肤</span>
      <span class="sw-caret" aria-hidden="true">▴</span>
    </button>`
  document.body.appendChild(box)

  const trigger = box.querySelector('.sw-trigger')
  let pop = null

  const close = () => {
    if (!pop) return
    pop.remove()
    pop = null
    trigger.setAttribute('aria-expanded', 'false')
    document.removeEventListener('mousedown', onDown)
    document.removeEventListener('keydown', onKey)
  }
  const onDown = (e) => { if (!box.contains(e.target)) close() }
  const onKey = (e) => { if (e.key === 'Escape') close() }

  const open = () => {
    pop = document.createElement('div')
    pop.className = 'sw-pop'
    pop.setAttribute('role', 'menu')
    pop.innerHTML = `
      <div class="sw-head"><b>设计语言</b><span>整套视觉 · ${SKINS.length} 选 1</span></div>
      <div class="sw-list">
        ${SKINS.map(s => `
          <button class="sw-item" type="button" role="menuitemradio"
                  aria-current="${s.id === PAGE_SKIN}" data-go="${s.id}">
            <span class="sw-dot" style="--sw-c:${s.chip}"></span>
            <span>${s.label}</span>
            <em>${s.en}</em>
          </button>`).join('')}
      </div>`
    box.appendChild(pop)
    trigger.setAttribute('aria-expanded', 'true')
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)

    pop.querySelectorAll('[data-go]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation()
        const id = btn.dataset.go
        if (id === PAGE_SKIN) { close(); return }
        saveSkin(id)
        // 落地页每套皮肤一个独立 HTML（六种版式无法靠 CSS 换肤）→ 这里是跳转
        const target = id === 'a' ? './index.html' : `./landing-${id}.html`
        // 用主题色遮罩过渡：先铺一层满屏色块再跳，避免白屏硬切
        transitionTo(target)
      })
    })
  }

  trigger.addEventListener('click', (e) => {
    e.stopPropagation()
    if (pop) close(); else open()
  })

  /* 跳转遮罩：色块自下而上盖满后导航 */
  function transitionTo(url) {
    if (REDUCE) { window.location.href = url; return }
    const veil = document.createElement('div')
    veil.style.cssText = [
      'position:fixed', 'inset:0', 'z-index:200', 'pointer-events:none',
      `background:${cur.chip}`, 'transform:scaleY(0)', 'transform-origin:bottom',
      'transition:transform .34s cubic-bezier(.19,1,.22,1)',
    ].join(';')
    document.body.appendChild(veil)
    requestAnimationFrame(() => { veil.style.transform = 'scaleY(1)' })
    window.setTimeout(() => { window.location.href = url }, 360)
  }

  /* 手速门挂在本按钮上：5 秒内连点 ≥6 下即触发（与旧版「主题按钮」同一手感） */
  return trigger
}

/* ============================================================ 2. 落笔处 + 彩蛋层 */
function mountEggNodes() {
  const pad = document.createElement('div')
  pad.className = 'ink-pad'
  pad.id = 'ink-pad'
  pad.title = '一处小小砚纸——试试写个字？'
  pad.innerHTML = `
    <i class="ip-g h" aria-hidden="true"></i>
    <i class="ip-g v" aria-hidden="true"></i>
    <span class="ip-label">落笔处</span>
    <canvas id="ip-canvas"></canvas>`
  document.body.appendChild(pad)

  const veil = document.createElement('div')
  veil.className = 'egg-veil hide'
  veil.id = 'egg-veil'
  veil.setAttribute('aria-hidden', 'true')
  veil.innerHTML = `
    <div class="egg-ink" aria-hidden="true"></div>
    <div class="egg-card">
      <span class="egg-seal" aria-hidden="true">匠</span>
      <p class="egg-line" id="egg-line"></p>
      <p class="egg-sub" id="egg-sub"></p>
      <div class="egg-actions">
        <button class="egg-go" id="egg-go" type="button">进去看看</button>
        <button class="egg-later" id="egg-later" type="button">先不急着进</button>
      </div>
    </div>`
  document.body.appendChild(veil)

  return { pad, veil }
}

/* ============================================================ 3. 入场编排 */
function runReveal() {
  const nodes = [...document.querySelectorAll('[data-reveal]')]
  if (!nodes.length) return
  if (REDUCE || !('IntersectionObserver' in window)) {
    nodes.forEach(n => n.classList.add('in'))
    return
  }
  const io = new IntersectionObserver((entries) => {
    entries.forEach(en => {
      if (!en.isIntersecting) return
      // 同屏多个元素按 DOM 顺序错峰 80ms
      const delay = nodes.indexOf(en.target) % 5 * 80
      window.setTimeout(() => en.target.classList.add('in'), delay)
      io.unobserve(en.target)
    })
  }, { rootMargin: '0px 0px -12% 0px', threshold: .12 })
  nodes.forEach(n => io.observe(n))
}

function runCounters() {
  const nodes = [...document.querySelectorAll('[data-count]')]
  if (!nodes.length) return
  const paint = (el, v) => { el.textContent = String(v) }
  if (REDUCE) { nodes.forEach(el => paint(el, el.dataset.count)); return }

  const io = new IntersectionObserver((entries) => {
    entries.forEach(en => {
      if (!en.isIntersecting) return
      const el = en.target
      io.unobserve(el)
      const target = Number(el.dataset.count) || 0
      const dur = 900
      const t0 = performance.now()
      const step = (now) => {
        const k = Math.min(1, (now - t0) / dur)
        // easeOutCubic：起手快、落定稳，比线性更像「读数停在刻度上」
        paint(el, Math.round(target * (1 - Math.pow(1 - k, 3))))
        if (k < 1) requestAnimationFrame(step)
      }
      requestAnimationFrame(step)
    })
  }, { threshold: .4 })
  nodes.forEach(el => io.observe(el))
}

function runTypewriter() {
  const nodes = [...document.querySelectorAll('[data-typewriter]')]
  if (!nodes.length || REDUCE) return
  nodes.forEach(node => {
    const full = node.textContent
    node.textContent = ''
    node.setAttribute('aria-label', full)
    let i = 0
    const tick = () => {
      node.textContent = full.slice(0, ++i)
      if (i < full.length) window.setTimeout(tick, 46)
    }
    window.setTimeout(tick, 380)
  })
}

/* ============================================================ 4. 彩蛋机关
   手速门：皮肤按钮 5 秒内连点 ≥6 下        → 编队调度局
   精读门：划选正文 ≥10 字并保持约 0.9s     → 查重捉虫
   书写门：在「落笔处」写成一个字            → 临帖墨试
   命中后先弹确认层，玩家自己决定进不进；解锁记录写 localStorage.lj_easter */
const EGGS = {
  dispatch: {
    file: 'easter/dispatch.html',
    line: '手速这么快，别浪费——来当主控吧。',
    sub: '彩蛋其一 · 编队调度局 · 60 秒派单挑战',
  },
  hunt: {
    file: 'easter/hunt.html',
    line: '读得这么仔细，风险一个都别想溜。',
    sub: '彩蛋其二 · 查重捉虫 · 45 秒校对挑战',
  },
  brush: {
    file: 'easter/brush.html',
    line: '横平竖直，一看就是练过的——来笔墨试一场。',
    sub: '彩蛋其三 · 临帖墨试 · 写个字，盖个章',
  },
}
const EGG_KEY = 'lj_easter'

function initEggs(trigger, { pad, veil }) {
  const cool = {}
  let pending = null
  let autoTimer = 0
  let selTimer = 0

  const read = () => {
    try { const v = localStorage.getItem(EGG_KEY); return v ? v.split(',') : [] } catch { return [] }
  }
  const render = () => {
    const n = read().length
    document.querySelectorAll('.egg-progress').forEach(el => {
      el.textContent = n ? `（已解锁 ${n}/3）` : ''
    })
  }
  const unlock = (key) => {
    const list = read()
    if (list.includes(key)) return
    list.push(key)
    try { localStorage.setItem(EGG_KEY, list.join(',')) } catch { /* 隐私模式忽略 */ }
    render()
    const name = String(EGGS[key]?.sub || '').split(' · ')[1] || ''
    toast(`解锁彩蛋 · ${name}`, '页边三则 · 集齐有惊喜')
  }
  const locked = (key) => Date.now() < (cool[key] || 0)

  const fire = (key, line) => {
    if (pending || locked(key)) return
    pending = key
    cool[key] = Date.now() + 1500   // 只防同一手势连发
    unlock(key)
    veil.querySelector('#egg-line').textContent = line || EGGS[key].line
    veil.querySelector('#egg-sub').textContent = EGGS[key].sub
    veil.classList.remove('hide', 'gone')
    veil.setAttribute('aria-hidden', 'false')
    clearTimeout(autoTimer)
    autoTimer = window.setTimeout(() => dismiss(1200), 10000)  // 无人操作 10s 自动收层
  }

  /* 收层即复位：无论下一步点击/按键是什么都刷新状态，马上可再次触发 */
  const dismiss = (coolMs) => {
    clearTimeout(autoTimer)
    if (!pending) return
    const key = pending
    pending = null
    cool[key] = Date.now() + (coolMs || 1200)
    veil.classList.add('hide')
    veil.setAttribute('aria-hidden', 'true')
    clearTimeout(selTimer)
  }

  veil.querySelector('#egg-go').addEventListener('click', () => {
    if (!pending) return
    const file = EGGS[pending].file
    veil.classList.add('gone')
    window.setTimeout(() => { window.location.href = file }, 460)
  })
  /* 除「进去看看」外：点到哪都收层复位 */
  veil.addEventListener('click', (e) => {
    if (e.target.closest?.('.egg-go')) return
    dismiss(1200)
  })
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') dismiss(1200) })
  render()

  /* ---- 手速门 ---- */
  let clicks = []
  let fireTimer = 0
  trigger.addEventListener('click', () => {
    const now = Date.now()
    clicks = clicks.filter(t => now - t < 5000)
    clicks.push(now)
    if (clicks.length >= 6 && !fireTimer) {
      // 留 260ms 缓冲，把用户正在连点的最后几下也数进去
      fireTimer = window.setTimeout(() => {
        fireTimer = 0
        const n = clicks.length
        clicks = []
        fire('dispatch', `五秒内连点 ${n} 下——手速这么快，别浪费，来当主控吧。`)
      }, 260)
    }
  })

  /* ---- 精读门 ---- */
  document.addEventListener('selectionchange', () => {
    if (pending) return
    clearTimeout(selTimer)
    const text = String(window.getSelection?.() || '').trim()
    if (text.length >= 10) selTimer = window.setTimeout(() => fire('hunt'), 900)
  })

  /* ---- 书写门 ----
     判定不认「写了什么」只认「写成了一个字」：墨迹外接框两个方向都撑开
     + 至少两笔 + 总笔迹够长（一 / 二 / 三 这类单薄横画天然被排除）。 */
  const canvas = pad.querySelector('#ip-canvas')
  const ctx = canvas.getContext('2d')
  let easy = false
  let cur = null
  let cleanTimer = 0
  let stats = null

  const clear = () => {
    ctx.save()
    ctx.setTransform(1, 0, 0, 1, 0, 0)
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.restore()
  }
  const resetStats = () => {
    stats = { strokes: 0, len: 0, minX: 1e9, minY: 1e9, maxX: -1e9, maxY: -1e9 }
    pad.classList.remove('half')
  }
  const fadeInk = () => {
    canvas.style.transition = 'opacity .45s ease'
    canvas.style.opacity = '0'
    window.setTimeout(() => {
      clear(); resetStats()
      canvas.style.transition = ''
      canvas.style.opacity = '1'
    }, 520)
  }
  const resize = () => {
    const w = pad.clientWidth, h = pad.clientHeight
    if (!w || !h) return
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    let old = null
    try { if (canvas.width) old = canvas.toDataURL() } catch { /* 忽略 */ }
    canvas.width = Math.round(w * dpr)
    canvas.height = Math.round(h * dpr)
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    if (old) {
      const img = new Image()
      img.onload = () => ctx.drawImage(img, 0, 0, w, h)
      img.src = old
    }
  }
  resetStats()
  resize()
  window.addEventListener('resize', resize)

  /* 悬停＝宽容模式：指针一进落笔处就降低判定门槛 */
  pad.addEventListener('pointerenter', () => { easy = true; pad.classList.add('easy') })
  pad.addEventListener('pointerleave', () => { easy = false; pad.classList.remove('easy') })

  const pos = (e) => {
    const r = canvas.getBoundingClientRect()
    return { x: e.clientX - r.left, y: e.clientY - r.top }
  }
  /* 墨色取本页正文色（--lb-fg），随皮肤走 */
  const ink = () => {
    const v = getComputedStyle(document.documentElement).getPropertyValue('--lb-fg').trim()
    return v || '#2E2823'
  }
  const looksLikeChar = () => {
    const h = pad.clientHeight || 1
    const spanX = stats.maxX - stats.minX
    const spanY = stats.maxY - stats.minY
    const minSpan = h * (easy ? 0.32 : 0.42)
    const minLen = h * (easy ? 0.8 : 1.1)
    return stats.strokes >= 2 && spanX >= minSpan && spanY >= minSpan && stats.len >= minLen
  }

  canvas.addEventListener('pointerdown', (e) => {
    if (pending) return
    e.preventDefault()
    easy = true
    pad.classList.add('easy')
    clearTimeout(cleanTimer)
    const p = pos(e)
    cur = { px: p.x, py: p.y, minX: p.x, maxX: p.x, minY: p.y, maxY: p.y, len: 0 }
    ctx.strokeStyle = ink()
    ctx.lineWidth = 10
    ctx.beginPath()
    ctx.moveTo(p.x, p.y)
    ctx.lineTo(p.x + 0.1, p.y)
    ctx.stroke()
    try { canvas.setPointerCapture(e.pointerId) } catch { /* 忽略 */ }
  })

  canvas.addEventListener('pointermove', (e) => {
    if (!cur) return
    const p = pos(e)
    ctx.beginPath()
    ctx.moveTo(cur.px, cur.py)
    ctx.lineTo(p.x, p.y)
    ctx.stroke()
    cur.len += Math.hypot(p.x - cur.px, p.y - cur.py)
    cur.px = p.x
    cur.py = p.y
    cur.minX = Math.min(cur.minX, p.x); cur.maxX = Math.max(cur.maxX, p.x)
    cur.minY = Math.min(cur.minY, p.y); cur.maxY = Math.max(cur.maxY, p.y)
  })

  const padUp = () => {
    if (!cur) return
    const s = cur
    cur = null
    if (s.len < 6) return            // 误点一下不算一笔
    stats.strokes += 1
    stats.len += s.len
    stats.minX = Math.min(stats.minX, s.minX); stats.maxX = Math.max(stats.maxX, s.maxX)
    stats.minY = Math.min(stats.minY, s.minY); stats.maxY = Math.max(stats.maxY, s.maxY)

    if (looksLikeChar()) {
      if (!locked('brush')) {
        pad.classList.add('count-3')
        window.setTimeout(() => {
          pad.classList.remove('count-3')
          fire('brush')
          fadeInk()                  // 弹层出现的同时，墨迹淡出消失
        }, 240)
      }
      return
    }
    const h = pad.clientHeight || 1
    if (stats.maxX - stats.minX >= h * 0.15 && stats.maxY - stats.minY >= h * 0.15) {
      pad.classList.add('half')      // 「快成了」的边框反馈
    }
    clearTimeout(cleanTimer)
    // 久未成字自动清纸：乱涂乱画不会把砚纸糊住
    cleanTimer = window.setTimeout(() => {
      if (cur || pending) return
      fadeInk()
    }, 20000)
  }
  canvas.addEventListener('pointerup', padUp)
  canvas.addEventListener('pointercancel', padUp)
  canvas.addEventListener('pointerleave', () => { if (cur) padUp() })
}

/* ============================================================ 启动 */
function boot() {
  document.documentElement.classList.remove('no-js')

  const nodes = mountEggNodes()
  const trigger = mountSkinSwitcher()

  runReveal()
  runCounters()
  runTypewriter()
  initEggs(trigger, nodes)

  // 指针特效：3D 倾斜 / 按钮磁吸 / 点击粒子（与以上互不干扰）
  initPointerFx()
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot)
} else {
  boot()
}

export { loadSkin }