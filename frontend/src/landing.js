import { initPointerFx, themeFlash, toast, reduceMotion } from './fx.js'

/* 论匠 LunJiang · v16 落地页：与工作台共用 tokens.css 主题令牌
   ---------------------------------------------------------------------------
   原生零依赖：主题选择器 / 柔化开关（写回 localStorage.lj_theme / lj_soft，
   并即时改写 documentElement 的 data-theme / data-soft）/ 切换反馈音 /
   入场动画 / 指标滚动 / 年份 / 三枚彩蛋。
   reduced-motion 的降级由 landing.css 兜底，这里只做能力探测。 */
(function () {
  'use strict'
  if (window.__ljLandingInit) return
  window.__ljLandingInit = true

  var root = document.documentElement
  root.classList.add('lj-js')

  /* ============================================================
     主题 / 柔化
     · 主题挂 <html data-theme>，六选一；柔化挂 <html data-soft>（on|off）
     · soft-cream / soft-mist 天生柔化：开关置灰并提示
     ============================================================ */
  var THEME_KEY = 'lj_theme'
  var SOFT_KEY = 'lj_soft'
  var THEMES = [
    { id: 'ops',         label: '暗色指挥舱', chip: '#3EE08F', alwaysSoft: false },
    { id: 'blueprint',   label: '蓝图工程',   chip: '#3E7FB8', alwaysSoft: false },
    { id: 'lab',         label: '实验记录本', chip: '#3B6EA5', alwaysSoft: false },
    { id: 'press',       label: '学术期刊',   chip: '#A32E24', alwaysSoft: false },
    { id: 'soft-cream',  label: '暖云手稿',   chip: '#D97742', alwaysSoft: true },
    { id: 'soft-mist',   label: '晨雾有机',   chip: '#6E93A8', alwaysSoft: true }
  ]

  var trigger = document.getElementById('theme-trigger')
  var picker = document.getElementById('theme-picker')
  var pop = document.getElementById('tp-pop')
  var grid = document.getElementById('tp-grid')
  var chipEl = document.getElementById('tp-chip')
  var labelEl = document.getElementById('tp-label')
  var softBtn = document.getElementById('tp-soft')
  var softNote = document.getElementById('tp-soft-note')

  function findTheme(id) {
    for (var i = 0; i < THEMES.length; i++) if (THEMES[i].id === id) return THEMES[i]
    return null
  }
  function read(key) {
    try { return localStorage.getItem(key) } catch (e) { return null }
  }
  function write(key, val) {
    try { localStorage.setItem(key, val) } catch (e) { /* 隐私模式忽略 */ }
  }

  var curTheme = findTheme(read(THEME_KEY)) ? read(THEME_KEY) : 'soft-cream'
  var softPref = read(SOFT_KEY) === 'off' ? 'off' : 'on'

  /* 极轻的切换反馈音：程序化生成，约 0.15s，全程 try/catch 兜底 */
  var audioCtx = null
  function blip() {
    try {
      var AC = window.AudioContext || window.webkitAudioContext
      if (!AC) return
      if (!audioCtx) audioCtx = new AC()
      if (audioCtx.state === 'suspended') audioCtx.resume()
      var t0 = audioCtx.currentTime
      var osc = audioCtx.createOscillator()
      var gain = audioCtx.createGain()
      osc.type = 'sine'
      osc.frequency.setValueAtTime(660, t0)
      osc.frequency.exponentialRampToValueAtTime(880, t0 + 0.12)
      gain.gain.setValueAtTime(0.0001, t0)
      gain.gain.exponentialRampToValueAtTime(0.05, t0 + 0.02)
      gain.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.15)
      osc.connect(gain)
      gain.connect(audioCtx.destination)
      osc.start(t0)
      osc.stop(t0 + 0.16)
    } catch (e) { /* 无音频能力时静默 */ }
  }

  /* 注入 6 个主题条目（色点为各主题强调色示例） */
  var itemEls = []
  if (grid) {
    for (var ti = 0; ti < THEMES.length; ti++) {
      ;(function (t) {
        var btn = document.createElement('button')
        btn.type = 'button'
        btn.className = 'tp-item'
        btn.setAttribute('role', 'menuitemradio')
        btn.title = t.label
        var chip = document.createElement('span')
        chip.className = 'chip'
        chip.style.background = t.chip
        var nm = document.createElement('span')
        nm.className = 'tp-name'
        nm.textContent = t.label
        var ck = document.createElement('span')
        ck.className = 'tp-check'
        ck.setAttribute('aria-hidden', 'true')
        ck.textContent = '✓'
        btn.appendChild(chip)
        btn.appendChild(nm)
        btn.appendChild(ck)
        btn.setAttribute('data-burst', '')
        btn.addEventListener('click', function () {
          var box = btn.getBoundingClientRect()
          var cx = box.left + box.width / 2
          var cy = box.top + box.height / 2
          if (reduceMotion()) { setTheme(t.id); return }   /* 减动效：直接切，不遮罩 */
          /* 全屏遮罩从条目中心扩散，盖满瞬间再换主题（揭幕） */
          themeFlash(cx, cy, function () { setTheme(t.id) })
        })
        grid.appendChild(btn)
        itemEls.push({ id: t.id, el: btn })
      })(THEMES[ti])
    }
  }

  /* 渲染：把状态同步到 <html> 与选择器 UI */
  function render() {
    var t = findTheme(curTheme) || THEMES[4]
    root.dataset.theme = t.id
    root.dataset.soft = t.alwaysSoft ? 'on' : softPref

    if (chipEl) chipEl.style.background = t.chip
    if (labelEl) labelEl.textContent = t.label
    for (var i = 0; i < itemEls.length; i++) {
      var on = itemEls[i].id === t.id
      itemEls[i].el.classList.toggle('on', on)
      itemEls[i].el.setAttribute('aria-checked', on ? 'true' : 'false')
    }
    if (softBtn) {
      softBtn.disabled = t.alwaysSoft
      var softOn = t.alwaysSoft || softPref === 'on'
      softBtn.classList.toggle('on', softOn)
      softBtn.setAttribute('aria-pressed', softOn ? 'true' : 'false')
    }
    if (softNote) {
      softNote.textContent = t.alwaysSoft ? '该主题天生柔化' : (softPref === 'on' ? '已开启' : '已关闭')
    }
  }

  function setTheme(id) {
    if (!findTheme(id) || id === curTheme) return
    curTheme = id
    write(THEME_KEY, id)
    render()
    blip()
  }

  function openPop(v) {
    if (!pop || !trigger) return
    pop.classList.toggle('open', v)
    trigger.setAttribute('aria-expanded', v ? 'true' : 'false')
  }

  if (trigger && pop) {
    trigger.addEventListener('click', function () {
      openPop(!pop.classList.contains('open'))
    })
    document.addEventListener('mousedown', function (e) {
      if (!pop.classList.contains('open')) return
      if (picker && picker.contains(e.target)) return
      openPop(false)
    })
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && pop.classList.contains('open')) openPop(false)
    })
  }

  if (softBtn) {
    softBtn.addEventListener('click', function () {
      var t = findTheme(curTheme)
      if (!t || t.alwaysSoft) return
      softPref = softPref === 'on' ? 'off' : 'on'
      write(SOFT_KEY, softPref)
      render()
      blip()
    })
  }

  render()

  /* ---- 入场动画：进入视口后加 .lj-in（CSS 侧控制位移与淡入） ---- */
  var reveals = document.querySelectorAll('.lj-reveal')
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.classList.add('lj-in')
          io.unobserve(en.target)
        }
      })
    }, { threshold: 0.15 })
    for (var r = 0; r < reveals.length; r++) io.observe(reveals[r])
  } else {
    for (var r2 = 0; r2 < reveals.length; r2++) reveals[r2].classList.add('lj-in')
  }

  /* ---- 指标滚动：进入视口后从 0 计数到目标（HTML 内置终值，无 JS 也可读） ---- */
  var prefersReduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  var counters = document.querySelectorAll('.num-v[data-count]')
  function countUp(el) {
    var target = parseFloat(el.getAttribute('data-count'))
    var t0 = performance.now()
    var dur = 900
    function step(now) {
      var p = Math.min((now - t0) / dur, 1)
      var eased = 1 - Math.pow(1 - p, 3)
      el.textContent = String(Math.round(target * eased))
      if (p < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  }
  if (!prefersReduce && 'IntersectionObserver' in window && counters.length) {
    for (var c = 0; c < counters.length; c++) counters[c].textContent = '0'
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          countUp(en.target)
          cio.unobserve(en.target)
        }
      })
    }, { threshold: 0.5 })
    for (var c2 = 0; c2 < counters.length; c2++) cio.observe(counters[c2])
  }

  /* ---- 页脚年份 ---- */
  var yearEl = document.getElementById('lj-year')
  if (yearEl) yearEl.textContent = String(new Date().getFullYear())

  /* ---- 英雄区打字机：逐字浮现（约 45ms/字，含闪烁光标，结束后移除）----
     · 把标题展平成字符序列，<em>「论文」的强调色在打字过程中保留
     · reduced-motion 环境：不拆分、不改 DOM，完整标题直接可见 */
  var heroTitle = document.querySelector('.hero h1')
  function heroFlat(node, isEm, out) {
    var kids = node.childNodes
    for (var i = 0; i < kids.length; i++) {
      var c = kids[i]
      if (c.nodeType === 3) {
        var s = c.nodeValue
        for (var j = 0; j < s.length; j++) out.push({ ch: s.charAt(j), em: isEm })
      } else if (c.nodeType === 1) {
        heroFlat(c, isEm || c.tagName === 'EM', out)
      }
    }
  }
  function heroType() {
    if (!heroTitle) return
    var flat = []
    heroFlat(heroTitle, false, flat)
    if (reduceMotion() || !flat.length) return

    heroTitle.setAttribute('aria-label', heroTitle.textContent)   /* 打字期间无障碍读全文 */
    heroTitle.textContent = ''
    var caret = document.createElement('i')
    caret.className = 'type-caret'
    caret.setAttribute('aria-hidden', 'true')

    var holder = null
    var holderEm = false
    var k = 0
    var timer = setInterval(function () {
      if (k >= flat.length) {
        clearInterval(timer)
        caret.remove()
        return
      }
      var it = flat[k++]
      if (!holder || holderEm !== it.em) {
        holder = document.createElement(it.em ? 'em' : 'span')
        holderEm = it.em
        heroTitle.appendChild(holder)
      }
      holder.appendChild(document.createTextNode(it.ch))
      heroTitle.appendChild(caret)
    }, 45)
  }
  setTimeout(heroType, 360)

  /* ============================================================
     彩蛋机关（三门 · 语义化触发）
     手速门：主题按钮 5 秒内连点 ≥6 下        → 编队调度局
     精读门：划选正文 ≥10 字并保持约 0.9s      → 查重捉虫
     书写门：在「落笔处」写成一个字即可        → 临帖墨试
     命中后先弹确认层，玩家自己决定进不进；解锁记录写 localStorage.lj_easter
     ============================================================ */
  var EGGS = {
    dispatch: { file: 'easter/dispatch.html', line: '手速这么快，别浪费——来当主控吧。', sub: '彩蛋其一 · 编队调度局 · 60 秒派单挑战' },
    hunt: { file: 'easter/hunt.html', line: '读得这么仔细，风险一个都别想溜。', sub: '彩蛋其二 · 查重捉虫 · 45 秒校对挑战' },
    brush: { file: 'easter/brush.html', line: '横平竖直，一看就是练过的——来笔墨试一场。', sub: '彩蛋其三 · 临帖墨试 · 写个字，盖个章' }
  }
  var EGG_KEY = 'lj_easter'
  var eggCool = {}
  var eggPending = null
  var eggVeil = document.getElementById('egg-veil')
  var eggAutoTimer = null
  var eggSelTimer = null

  function eggsRead() {
    try { var v = localStorage.getItem(EGG_KEY); return v ? v.split(',') : [] } catch (e) { return [] }
  }
  function eggsRender() {
    var list = eggsRead()
    var nodes = document.querySelectorAll('.egg-progress')
    var txt = list.length ? '（已解锁 ' + list.length + '/3）' : ''
    for (var i = 0; i < nodes.length; i++) nodes[i].textContent = txt
  }
  function eggsUnlock(key) {
    var list = eggsRead()
    if (list.indexOf(key) < 0) {
      list.push(key)
      try { localStorage.setItem(EGG_KEY, list.join(',')) } catch (e) { /* 忽略 */ }
      eggsRender()
      /* 解锁即弹成就提示：名字取现有文案（sub 中段） */
      var eggName = String((EGGS[key] || {}).sub || '').split(' · ')[1] || ''
      toast('解锁彩蛋 · ' + eggName, '页边三则 · 集齐有惊喜')
    }
  }
  function eggLocked(key) { return Date.now() < (eggCool[key] || 0) }
  function eggFire(key, line) {
    if (!eggVeil || eggPending || eggLocked(key)) return
    eggPending = key
    eggCool[key] = Date.now() + 1500   /* 只防同一手势连发，稍后即可再次触发 */
    eggsUnlock(key)
    document.getElementById('egg-line').textContent = line || EGGS[key].line
    document.getElementById('egg-sub').textContent = EGGS[key].sub
    eggVeil.classList.remove('hide', 'gone')
    eggVeil.setAttribute('aria-hidden', 'false')
    clearTimeout(eggAutoTimer)
    eggAutoTimer = setTimeout(function () { eggDismiss(1200) }, 10000)   /* 无人操作 10s 自动收层 */
  }
  /* 收层即复位：无论用户下一步点击/按键是什么，都自动刷新状态，马上可以再次触发 */
  function eggDismiss(coolMs) {
    clearTimeout(eggAutoTimer)
    if (!eggPending) return
    var key = eggPending
    eggPending = null
    eggCool[key] = Date.now() + (coolMs || 1200)
    eggVeil.classList.add('hide')
    eggVeil.setAttribute('aria-hidden', 'true')
    clearTimeout(eggSelTimer)   /* 旧选区不立刻二次命中精读门 */
  }
  if (eggVeil) {
    document.getElementById('egg-go').addEventListener('click', function () {
      if (!eggPending) return
      var file = EGGS[eggPending].file
      eggVeil.classList.add('gone')
      setTimeout(function () { location.href = file }, 460)
    })
    /* 除「进去看看」外：点到哪都收层复位（含卡片正文与「先不急着进」） */
    eggVeil.addEventListener('click', function (e) {
      if (e.target && e.target.closest && e.target.closest('.egg-go')) return
      eggDismiss(1200)
    })
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') eggDismiss(1200)
    })
  }
  eggsRender()

  /* 手速门：主题按钮 5 秒内连点 6 下及以上（触发文案带上实际手速）
     命中后留 260ms 缓冲，把用户正在连点的最后几下也数进去 */
  var eggClicks = []
  var eggFireTimer = null
  if (trigger) {
    trigger.addEventListener('click', function () {
      var now = Date.now()
      var keep = []
      for (var i = 0; i < eggClicks.length; i++) if (now - eggClicks[i] < 5000) keep.push(eggClicks[i])
      keep.push(now)
      eggClicks = keep
      if (eggClicks.length >= 6 && !eggFireTimer) {
        eggFireTimer = setTimeout(function () {
          eggFireTimer = null
          var n = eggClicks.length
          eggClicks = []
          eggFire('dispatch', '五秒内连点 ' + n + ' 下——手速这么快，别浪费，来当主控吧。')
        }, 260)
      }
    })
  }

  /* 精读门：划选正文 ≥10 字并保持 */
  document.addEventListener('selectionchange', function () {
    if (eggPending) return
    clearTimeout(eggSelTimer)
    var sel = window.getSelection()
    var text = sel ? String(sel).trim() : ''
    if (text.length >= 10) {
      eggSelTimer = setTimeout(function () { eggFire('hunt') }, 900)
    }
  })

  /* 书写门：落笔处（悬停即宽容）
     - 判定不认「写了什么」只认「写成了一个字」：墨迹外接框两个方向都撑开
       + 至少两笔 + 总笔迹够长（一 / 二 / 三 这类单薄横画天然被排除）
     - 悬停落笔处：门槛再降一档
     - 弹窗后墨迹自动淡出；久未成字也自动清纸，乱涂乱画不会把砚纸糊住 */
  var pad = document.getElementById('ink-pad')
  var padCanvas = document.getElementById('ip-canvas')
  var padCtx = padCanvas ? padCanvas.getContext('2d') : null
  var padEasy = false
  var padCur = null
  var padCleanTimer = null
  var padStats = null

  function padClear() {
    if (!padCtx || !padCanvas) return
    padCtx.save()
    padCtx.setTransform(1, 0, 0, 1, 0, 0)
    padCtx.clearRect(0, 0, padCanvas.width, padCanvas.height)
    padCtx.restore()
  }
  function padResetStats() {
    padStats = { strokes: 0, len: 0, minX: 1e9, minY: 1e9, maxX: -1e9, maxY: -1e9 }
    if (pad) pad.classList.remove('half')
  }
  /* 墨迹淡出：弹窗出现 / 久未成字时，纸上的字自动消失 */
  function padFadeInk() {
    if (!padCanvas) return
    padCanvas.style.transition = 'opacity 0.45s ease'
    padCanvas.style.opacity = '0'
    setTimeout(function () {
      padClear()
      padResetStats()
      padCanvas.style.transition = ''
      padCanvas.style.opacity = '1'
    }, 520)
  }
  function padResize() {
    if (!padCanvas || !padCtx || !pad) return
    var w = pad.clientWidth, h = pad.clientHeight
    if (!w || !h) return
    var dpr = window.devicePixelRatio || 1
    var old = null
    try { if (padCanvas.width) old = padCanvas.toDataURL() } catch (e) { /* 忽略 */ }
    padCanvas.width = Math.round(w * dpr)
    padCanvas.height = Math.round(h * dpr)
    padCtx.setTransform(dpr, 0, 0, dpr, 0, 0)
    padCtx.lineCap = 'round'
    padCtx.lineJoin = 'round'
    if (old) {
      var img = new Image()
      img.onload = function () { padCtx.drawImage(img, 0, 0, w, h) }
      img.src = old
    }
  }
  if (pad && padCanvas && padCtx) {
    padResetStats()
    padResize()
    window.addEventListener('resize', padResize)

    /* 悬停＝宽容模式：鼠标一进落笔处就降低判定门槛 */
    pad.addEventListener('pointerenter', function () { padEasy = true; pad.classList.add('easy') })
    pad.addEventListener('pointerleave', function () { padEasy = false; pad.classList.remove('easy') })

    var padPos = function (e) {
      var r = padCanvas.getBoundingClientRect()
      return { x: e.clientX - r.left, y: e.clientY - r.top }
    }
    /* 墨色取当前主题正文色（--text），随主题切换 */
    var padInk = function () {
      try { return getComputedStyle(root).getPropertyValue('--text').trim() || '#2E2823' } catch (e) { return '#2E2823' }
    }
    /* 判定：像「一个字」就行，不看具体写了什么 */
    function padLooksLikeChar() {
      var h = pad.clientHeight || 1
      var spanX = padStats.maxX - padStats.minX
      var spanY = padStats.maxY - padStats.minY
      /* 字是方的：两个方向都要相对画布高度撑开——一/二/三 撑不开高度，天然排除 */
      var minSpan = h * (padEasy ? 0.32 : 0.42)
      var minLen = h * (padEasy ? 0.8 : 1.1)
      return padStats.strokes >= 2 && spanX >= minSpan && spanY >= minSpan && padStats.len >= minLen
    }
    padCanvas.addEventListener('pointerdown', function (e) {
      if (eggPending) return
      e.preventDefault()
      padEasy = true
      pad.classList.add('easy')
      clearTimeout(padCleanTimer)
      var p = padPos(e)
      padCur = { px: p.x, py: p.y, minX: p.x, maxX: p.x, minY: p.y, maxY: p.y, len: 0 }
      padCtx.strokeStyle = padInk()
      padCtx.lineWidth = 10
      padCtx.beginPath()
      padCtx.moveTo(p.x, p.y)
      padCtx.lineTo(p.x + 0.1, p.y)
      padCtx.stroke()
      try { padCanvas.setPointerCapture(e.pointerId) } catch (err) { /* 忽略 */ }
    })
    padCanvas.addEventListener('pointermove', function (e) {
      if (!padCur) return
      var p = padPos(e)
      padCtx.beginPath()
      padCtx.moveTo(padCur.px, padCur.py)
      padCtx.lineTo(p.x, p.y)
      padCtx.stroke()
      padCur.len += Math.hypot(p.x - padCur.px, p.y - padCur.py)
      padCur.px = p.x
      padCur.py = p.y
      if (p.x < padCur.minX) padCur.minX = p.x
      if (p.x > padCur.maxX) padCur.maxX = p.x
      if (p.y < padCur.minY) padCur.minY = p.y
      if (p.y > padCur.maxY) padCur.maxY = p.y
    })
    var padUp = function () {
      if (!padCur) return
      var s = padCur
      padCur = null
      if (s.len < 6) return   /* 误点一下不算一笔 */
      /* 并入总统计：跨笔画累计，不看单笔形状 */
      padStats.strokes += 1
      padStats.len += s.len
      if (s.minX < padStats.minX) padStats.minX = s.minX
      if (s.maxX > padStats.maxX) padStats.maxX = s.maxX
      if (s.minY < padStats.minY) padStats.minY = s.minY
      if (s.maxY > padStats.maxY) padStats.maxY = s.maxY

      if (padLooksLikeChar()) {
        if (!eggLocked('brush')) {
          pad.classList.add('count-3')
          setTimeout(function () {
            pad.classList.remove('count-3')
            eggFire('brush')
            padFadeInk()   /* 对话框弹出的同时，墨迹淡出消失 */
          }, 240)
        }
        return   /* 冷却期内的重写：保留墨迹与统计，冷却一过再落一笔即可触发 */
      }
      /* 尚未成字：给「快成了」的边框反应，并安排久未成字时的自动清纸 */
      var h = pad.clientHeight || 1
      if (padStats.maxX - padStats.minX >= h * 0.15 && padStats.maxY - padStats.minY >= h * 0.15) {
        pad.classList.add('half')
      }
      clearTimeout(padCleanTimer)
      padCleanTimer = setTimeout(function () {
        if (padCur || eggPending) return
        padFadeInk()
      }, 20000)
    }
    padCanvas.addEventListener('pointerup', padUp)
    padCanvas.addEventListener('pointercancel', padUp)
    padCanvas.addEventListener('pointerleave', function () {
      if (padCur) padUp()   /* capture 未生效时兜底结笔 */
    })
  }

  /* ---- 指针特效：3D 倾斜 [data-tilt] / 按钮磁吸 [data-magnet] / 点击粒子 [data-burst]
     与以上滚动揭示、彩蛋机关互不干扰，仅在末尾追加初始化。
     注：不含任何跟随光标的拖尾 / 光晕 —— 光标样式留给后续自定义需求。 */
  initPointerFx()
})()
