/* 论匠落地页 · 原生交互（v15 · ROUND15）
   零依赖，总预算 <3KB：主题切换 / 入场动画 / 数字滚动 / 年份。
   reduced-motion 的降级由 landing.css 的媒体查询兜底，这里不做能力探测。 */
(function () {
  'use strict'
  /* 防重复执行：脚本若被二次挂载，监听器会叠加导致判定错乱 */
  if (window.__ljLandingInit) return
  window.__ljLandingInit = true

  /* ---- 主题切换：v15 六主题（亮·天青 / 暗·玄墨 / 墨格编辑部 / 新构成主义 / 夜航诗意 / 拓印套色）
         持久化到 localStorage（lj_landing_theme）。
         light/dark 显示经典六段结构（#ln-site）；h/i/j/k 显示编辑部版式（#ed-site）。
         循环切换：light → dark → h → i → j → k → light，按钮 label 显示「下一档」。
         两套结构各有一个 .ln-theme-btn（经典导航 / 期刊头）：进入编辑部版式后
         #ln-site 整体隐藏，若期刊头不带按钮，页面上将没有任何主题入口（曾导致
         切进 h/i/j/k 后无法切回），故按钮必须成对存在。 ---- */
  var KEY = 'lj_landing_theme'
  var ORDER = ['light', 'dark', 'h', 'i', 'j', 'k']
  var NEXT_LABEL = { light: '暗色', dark: '墨格', h: '构成', i: '夜航', j: '套色', k: '亮色' }
  var apply = function (t) {
    if (ORDER.indexOf(t) < 0) t = 'light'
    document.body.dataset.theme = t
    var modern = t !== 'light' && t !== 'dark'
    var ed = document.getElementById('ed-site')
    var ln = document.getElementById('ln-site')
    if (ed) ed.style.display = modern ? '' : 'none'
    if (ln) ln.style.display = modern ? 'none' : ''
    var labels = document.querySelectorAll('.ln-theme-label')
    for (var i = 0; i < labels.length; i++) labels[i].textContent = NEXT_LABEL[t] || ''
    try { localStorage.setItem(KEY, t) } catch { /* 隐私模式忽略 */ }
  }
  var saved = null
  try { saved = localStorage.getItem(KEY) } catch { /* 忽略 */ }
  apply(ORDER.indexOf(saved) >= 0 ? saved : 'light')
  var btns = document.querySelectorAll('.ln-theme-btn')
  for (var b = 0; b < btns.length; b++) {
    btns[b].addEventListener('click', function () {
      var cur = ORDER.indexOf(document.body.dataset.theme)
      apply(ORDER[(cur + 1) % ORDER.length])
    })
  }

  /* ---- 入场动画：进入视口后加 .ln-in（CSS 侧带 stagger 延迟） ---- */
  var reveals = document.querySelectorAll('.ln-reveal')
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.classList.add('ln-in')
          io.unobserve(en.target)
        }
      })
    }, { threshold: 0.15 })
    reveals.forEach(function (el) { io.observe(el) })
  } else {
    reveals.forEach(function (el) { el.classList.add('ln-in') })
  }

  /* ---- 数字滚动：评测指标进入视口后从 0 计数到目标 ---- */
  var counters = document.querySelectorAll('.ln-num[data-count]')
  var animate = function (el) {
    var target = parseFloat(el.getAttribute('data-count'))
    var dur = 900
    var t0 = performance.now()
    var step = function (now) {
      var p = Math.min((now - t0) / dur, 1)
      var eased = 1 - Math.pow(1 - p, 3)
      el.textContent = String(Math.round(target * eased))
      if (p < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  }
  if ('IntersectionObserver' in window) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          animate(en.target)
          cio.unobserve(en.target)
        }
      })
    }, { threshold: 0.5 })
    counters.forEach(function (el) { cio.observe(el) })
  } else {
    counters.forEach(function (el) { el.textContent = el.getAttribute('data-count') })
  }

  /* ---- 页脚年份 ---- */
  var year = document.getElementById('ln-year')
  if (year) year.textContent = String(new Date().getFullYear())

  /* ============================================================
     彩蛋机关（三门 · 语义化触发）
     手速门：5 秒内连点主题按钮 ≥6 下       → 编队调度局（文案报出实际手速）
     精读门：划选正文 ≥10 字并保持约 0.9s   → 查重捉虫（逐字读过，才看得见风险）
     书写门：在「落笔处」写成一个字即可     → 临帖墨试（一/二/三式单薄横画不算）
     命中后先弹俏皮话确认层，玩家自己决定进不进；解锁记录写 localStorage.lj_easter
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
  /* 收层即复位：出现弹窗后，无论用户下一步点击/按键是什么，
     都自动刷新状态（清冷却、清选区计时），马上可以再次触发 */
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
  var eggBtns = document.querySelectorAll('.ln-theme-btn')
  for (var eb = 0; eb < eggBtns.length; eb++) {
    eggBtns[eb].addEventListener('click', function () {
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
  var eggSelTimer = null
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
    var padInk = function () {
      try { return getComputedStyle(document.body).getPropertyValue('--ln-ink').trim() || '#1A1815' } catch (e) { return '#1A1815' }
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
})()
