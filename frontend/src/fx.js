/* ============================================================
   v17 · 动效工具箱（落地页 landing.js 与工作台 React 共用）
   —— 点击粒子 / 主题切换全屏过渡 / 成就提示条 / 元素级指针特效

   设计约束：
     · 颜色一律从 tokens.css 变量读取，不硬编码主题色
     · 尊重 prefers-reduced-motion：命中时全部降级（不产生运动）
     · 粒子节点靠 animationend 自动回收，无残留定时器
     · 指针特效只做「与元素绑定」的交互：3D 倾斜（含高光扫过）+ 按钮磁吸；
       不做任何跟随光标的拖尾 / 光晕——光标样式留给后续自定义需求

   导出：
     initPointerFx()   → 初始化元素级指针特效，返回 dispose()
     burstAt(x, y)     → 在坐标处迸发一圈粒子
     themeFlash(x, y, onCover) → 全屏圆形遮罩过渡，onCover 在盖满瞬间回调
     toast(main, sub)  → 顶部成就提示条
     reduceMotion()    → 当前是否处于「减少动态效果」环境
   ============================================================ */

export function reduceMotion() {
  return window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false
}

const finePointer = () =>
  window.matchMedia ? window.matchMedia('(pointer: fine)').matches : true

/* ---------------------------------------------------------- 图层单例 */
let layer = null
function getLayer() {
  if (layer && document.body.contains(layer)) return layer
  layer = document.createElement('div')
  layer.className = 'fx-layer'
  layer.setAttribute('aria-hidden', 'true')
  document.body.appendChild(layer)
  return layer
}

function token(name, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return v || fallback
}

/* ---------------------------------------------------------- 点击粒子爆发 */
export function burstAt(x, y, count = 20) {
  if (reduceMotion()) return
  const host = getLayer()
  const frag = document.createDocumentFragment()
  for (let i = 0; i < count; i++) {
    const dot = document.createElement('i')
    dot.className = 'fx-spark'
    const angle = (Math.PI * 2 * i) / count + Math.random() * 0.45
    const dist = 26 + Math.random() * 52
    dot.style.setProperty('--tx', `${Math.cos(angle) * dist}px`)
    dot.style.setProperty('--ty', `${Math.sin(angle) * dist}px`)
    const size = 3 + Math.random() * 3.5
    dot.style.width = `${size}px`
    dot.style.height = `${size}px`
    dot.style.left = `${x}px`
    dot.style.top = `${y}px`
    // 约 1/4 用次强调色，其余用主强调色
    dot.style.background = Math.random() > 0.74 ? 'var(--accent-2)' : 'var(--accent)'
    dot.addEventListener('animationend', () => dot.remove(), { once: true })
    frag.appendChild(dot)
  }
  host.appendChild(frag)
}

/* ---------------------------------------------------------- 主题切换全屏过渡 */
export function themeFlash(x, y, onCover) {
  const done = typeof onCover === 'function' ? onCover : () => {}
  if (reduceMotion()) { done(); return }
  const host = getLayer()
  const el = document.createElement('div')
  el.className = 'fx-flash'
  // 半径取到最远角，保证扩散后完全盖住视口
  const r = Math.hypot(
    Math.max(x, window.innerWidth - x),
    Math.max(y, window.innerHeight - y),
  )
  el.style.left = `${x}px`
  el.style.top = `${y}px`
  el.style.width = `${r * 2}px`
  el.style.height = `${r * 2}px`
  el.style.marginLeft = `${-r}px`
  el.style.marginTop = `${-r}px`
  el.style.setProperty('--flash-c', token('--accent', '#D97742'))
  host.appendChild(el)
  // 遮罩盖满的瞬间切换主题，形成「揭幕」效果
  const coverAt = reduceMotion() ? 0 : 230
  window.setTimeout(done, coverAt)
  el.addEventListener('animationend', () => el.remove(), { once: true })
}

/* ---------------------------------------------------------- 成就提示条 */
let achEl = null
let achTimer = 0
function ensureToast() {
  if (achEl && document.body.contains(achEl)) return achEl
  achEl = document.createElement('div')
  achEl.className = 'ach-bar'
  achEl.setAttribute('role', 'status')
  achEl.innerHTML = '<span class="ach-dot" aria-hidden="true"></span>'
    + '<span class="ach-body"><b class="ach-main"></b><em class="ach-sub"></em></span>'
  document.body.appendChild(achEl)
  return achEl
}

export function toast(main, sub = '') {
  const bar = ensureToast()
  bar.querySelector('.ach-main').textContent = main
  const subEl = bar.querySelector('.ach-sub')
  subEl.textContent = sub
  subEl.style.display = sub ? '' : 'none'
  bar.classList.remove('show')
  // 强制回流，保证连续触发时动画能重放
  void bar.offsetWidth
  bar.classList.add('show')
  window.clearTimeout(achTimer)
  achTimer = window.setTimeout(() => bar.classList.remove('show'), 2800)
}

/* ---------------------------------------------------------- 指针特效 */
/**
 * 3D 倾斜：[data-tilt] —— 按指针在元素内的位置计算 rotateX/rotateY，
 *   并写入 --mx/--my 供高光扫过（CSS 侧用）。
 * 按钮磁吸：[data-magnet] —— 指针进入后朝指针轻微位移（上限 8px）。
 * 注：不做任何「跟随光标」的拖尾 / 光晕类效果——光标样式留给后续自定义需求，
 *     这里只保留与元素绑定的交互（倾斜 / 磁吸）与点击反馈（粒子爆发）。
 */
export function initPointerFx() {
  const noMotion = reduceMotion()

  let tiltEl = null
  let magnetEl = null

  const resetTilt = () => {
    if (!tiltEl) return
    tiltEl.classList.remove('tilt-on')
    tiltEl.style.removeProperty('--rx')
    tiltEl.style.removeProperty('--ry')
    tiltEl.style.removeProperty('--mx')
    tiltEl.style.removeProperty('--my')
    tiltEl = null
  }

  const resetMagnet = () => {
    if (!magnetEl) return
    magnetEl.style.removeProperty('--mgx')
    magnetEl.style.removeProperty('--mgy')
    magnetEl = null
  }

  const onMove = (e) => {
    /* 3D 倾斜 */
    const t = e.target instanceof Element ? e.target.closest('[data-tilt]') : null
    if (t !== tiltEl) {
      resetTilt()
      if (t) { tiltEl = t; t.classList.add('tilt-on') }
    }
    if (tiltEl) {
      const r = tiltEl.getBoundingClientRect()
      const px = (e.clientX - r.left) / r.width
      const py = (e.clientY - r.top) / r.height
      tiltEl.style.setProperty('--ry', `${(px - 0.5) * 14}deg`)
      tiltEl.style.setProperty('--rx', `${(0.5 - py) * 12}deg`)
      tiltEl.style.setProperty('--mx', `${px * 100}%`)
      tiltEl.style.setProperty('--my', `${py * 100}%`)
    }

    /* 按钮磁吸 */
    const m = e.target instanceof Element ? e.target.closest('[data-magnet]') : null
    if (m !== magnetEl) {
      resetMagnet()
      if (m) magnetEl = m
    }
    if (magnetEl) {
      const r = magnetEl.getBoundingClientRect()
      const cx = r.left + r.width / 2
      const cy = r.top + r.height / 2
      const dx = Math.max(-8, Math.min(8, (e.clientX - cx) * 0.06))
      const dy = Math.max(-8, Math.min(8, (e.clientY - cy) * 0.08))
      magnetEl.style.setProperty('--mgx', `${dx}px`)
      magnetEl.style.setProperty('--mgy', `${dy}px`)
    }
  }

  const onLeave = () => {
    resetTilt()
    resetMagnet()
  }

  /* 点击粒子：带 data-burst 的元素在点击处迸发 */
  const onClick = (e) => {
    const t = e.target instanceof Element ? e.target.closest('[data-burst]') : null
    if (t) burstAt(e.clientX, e.clientY)
  }

  if (!noMotion && finePointer()) {
    document.addEventListener('pointermove', onMove, { passive: true })
    document.addEventListener('pointerleave', onLeave)
  }
  document.addEventListener('click', onClick)

  return function dispose() {
    document.removeEventListener('pointermove', onMove)
    document.removeEventListener('pointerleave', onLeave)
    document.removeEventListener('click', onClick)
    resetTilt()
    resetMagnet()
  }
}