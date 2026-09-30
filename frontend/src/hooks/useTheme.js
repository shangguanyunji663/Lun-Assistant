import { useEffect, useRef, useState } from 'react'

/* v11 · 四主题切换（A 柔雾青绿 / B 黑白瑞士 / C 暗墨夜山 / D 青绿金碧）
   v13 · 新增 E 雨过天青 / F 玄墨赭金 / G 秋香宣纸（注册与切换机制和四主题完全一致）
   v15 · 现代艺术四主题 H 墨格编辑部 / I 新构成主义 / J 夜航诗意 / K 拓印套色
   （样式见 styles.css「v15 · 现代艺术四主题」节；旧 7 版零改动共存） */
export const THEMES = [
  { id: 'a', label: '柔雾青绿', chip: '#C5DBE8' },
  { id: 'b', label: '黑白瑞士', chip: '#000000' },
  { id: 'c', label: '暗墨夜山', chip: '#0A1424' },
  { id: 'd', label: '青绿金碧', chip: '#C9B58A' },
  // v13 · 新增三主题（样式见 styles.css「v13 · 新增三主题」节）
  { id: 'e', label: '雨过天青', chip: '#C7D3CB' },
  { id: 'f', label: '玄墨赭金', chip: '#171512' },
  { id: 'g', label: '秋香宣纸', chip: '#E6DECB' },
  // v15 · 现代艺术四主题（编辑部 / 构成主义 / 夜航 / 套色）
  { id: 'h', label: '墨格编辑部', chip: '#C8341F' },
  { id: 'i', label: '新构成主义', chip: '#2B4BC7' },
  { id: 'j', label: '夜航诗意', chip: '#0B0C10' },
  { id: 'k', label: '拓印套色', chip: '#FF48B0' },
]

const VALID_THEMES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k']
const INK_MIN = 0
const INK_MAX = 0.4
const INK_DEFAULT = 0.16

const loadTheme = () => {
  const t = localStorage.getItem('lj_theme')
  return VALID_THEMES.includes(t) ? t : 'a'
}

const loadInkOp = () => {
  // 缺失 / 空串 ≠ 显式 0：Number(null)=0、Number('')=0 会蒙混过 >=INK_MIN 校验，
  // 曾导致新访客山水底图默认不显示；此处先回落默认，再做数值区间校验。
  const raw = localStorage.getItem('lj_ink_op')
  if (raw === null || raw.trim() === '') return INK_DEFAULT
  const v = Number(raw)
  return Number.isFinite(v) && v >= INK_MIN && v <= INK_MAX ? v : INK_DEFAULT
}

/**
 * 主题 + 山水浓度：
 * - 两者持久化到 localStorage（裸字符串格式，与 console/tuner.html 调参台互通）；
 * - 监听 storage 事件实现跨 tab 实时联动；
 * - 主题切换时播放程序化"卷轴松开"咔哒声（Web Audio API，零外部资产）。
 */
export function useTheme() {
  const [theme, setTheme] = useState(loadTheme)
  const [inkOp, setInkOp] = useState(loadInkOp)
  // 首次 mount 时不响（避免 reload 主题后立刻播放）
  const themeTickRef = useRef(false)

  useEffect(() => {
    document.body.dataset.theme = theme
    try { localStorage.setItem('lj_theme', theme) } catch { /* 隐私模式忽略 */ }
    // 主题切换音效：仅在用户已与页面交互后（autoplay 策略），try/catch 兜隐私模式 / iOS 静音
    if (themeTickRef.current) {
      try {
        const AC = window.AudioContext || window.webkitAudioContext
        if (AC) {
          const ac = new AC()
          const osc = ac.createOscillator()
          const gain = ac.createGain()
          osc.type = 'triangle'
          osc.frequency.setValueAtTime(880, ac.currentTime)
          osc.frequency.exponentialRampToValueAtTime(220, ac.currentTime + 0.15)
          gain.gain.setValueAtTime(0.06, ac.currentTime)
          gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 0.18)
          osc.connect(gain).connect(ac.destination)
          osc.start(ac.currentTime)
          osc.stop(ac.currentTime + 0.20)
          setTimeout(() => ac.close(), 250)
        }
      } catch { /* autoplay blocked or audio disabled */ }
    }
    themeTickRef.current = true
  }, [theme])

  useEffect(() => {
    document.documentElement.style.setProperty('--ink-photo-op', String(inkOp))
    try { localStorage.setItem('lj_ink_op', String(inkOp)) } catch { /* 隐私模式忽略 */ }
  }, [inkOp])

  /* 调参台联动：用户在 console/tuner.html 改 lj_theme / lj_ink_op 后主应用实时生效 */
  useEffect(() => {
    const onStorage = (e) => {
      if (e.key === 'lj_theme' && VALID_THEMES.includes(e.newValue)) {
        setTheme(e.newValue)
      } else if (e.key === 'lj_ink_op') {
        // 他页删除该键时 newValue 为 null：回落默认（与 loadInkOp 缺失处理一致）
        if (e.newValue === null) { setInkOp(INK_DEFAULT) } else {
          const v = Number(e.newValue)
          if (Number.isFinite(v) && v >= INK_MIN && v <= INK_MAX) setInkOp(v)
        }
      }
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  return { theme, setTheme, inkOp, setInkOp, THEMES }
}
