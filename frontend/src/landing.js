/* 论匠落地页 · 原生交互（v15 · ROUND15）
   零依赖，总预算 <3KB：主题切换 / 入场动画 / 数字滚动 / 年份。
   reduced-motion 的降级由 landing.css 的媒体查询兜底，这里不做能力探测。 */
(function () {
  'use strict'

  /* ---- 主题切换：v15 六主题（亮·天青 / 暗·玄墨 / 墨格编辑部 / 新构成主义 / 夜航诗意 / 拓印套色）
         持久化到 localStorage（lj_landing_theme）。
         light/dark 显示经典六段结构（#ln-site）；h/i/j/k 显示编辑部版式（#ed-site）。
         循环切换：light → dark → h → i → j → k → light，按钮 label 显示「下一档」。 ---- */
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
    var label = document.querySelector('.ln-theme-label')
    if (label) label.textContent = NEXT_LABEL[t] || ''
    try { localStorage.setItem(KEY, t) } catch { /* 隐私模式忽略 */ }
  }
  var saved = null
  try { saved = localStorage.getItem(KEY) } catch { /* 忽略 */ }
  apply(ORDER.indexOf(saved) >= 0 ? saved : 'light')
  var btn = document.getElementById('ln-theme')
  if (btn) {
    btn.addEventListener('click', function () {
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
})()
