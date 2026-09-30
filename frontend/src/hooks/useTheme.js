import { useCallback, useEffect, useState } from 'react'

/* ============================================================
   v16 主题体系（取代旧 11 套水墨主题）
     · 6 个主题：前四个（ops/blueprint/lab/press）各带「锐 / 柔」两态；
       soft-cream / soft-mist 为天生柔主题，仅配色不同。
     · 柔化开关只改材质与配色（tokens.css 里切换 [data-soft]），不动结构。
     · 主题属性挂在 <html>，两页（落地页 / 工作台）共用同一份 localStorage。
   ============================================================ */

export const THEMES = [
  { id: 'ops', label: '暗色指挥舱', chip: '#3EE08F', soft: true },
  { id: 'blueprint', label: '蓝图工程', chip: '#0E3556', soft: true },
  { id: 'lab', label: '实验记录本', chip: '#F8F2E4', soft: true },
  { id: 'press', label: '学术期刊', chip: '#A32E24', soft: true },
  { id: 'soft-cream', label: '暖云手稿', chip: '#D97742', soft: false },
  { id: 'soft-mist', label: '晨雾有机', chip: '#6E93A8', soft: false },
]

const VALID = THEMES.map(t => t.id)
/** 天生柔主题：不存在「锐」态，柔化开关对其置灰 */
export const isAlwaysSoft = (id) => ['soft-cream', 'soft-mist'].includes(id)

const LS_THEME = 'lj_theme'
const LS_SOFT = 'lj_soft'

const loadTheme = () => {
  const t = localStorage.getItem(LS_THEME)
  return VALID.includes(t) ? t : 'soft-cream'
}

const loadSoft = (theme) => {
  if (isAlwaysSoft(theme)) return true
  const v = localStorage.getItem(LS_SOFT)
  if (v === null || v === '') return true            // 默认柔化
  return v === 'on'
}

/**
 * 主题 + 柔化开关：
 * - 写入 <html data-theme data-soft>，并持久化到 localStorage；
 * - 监听 storage 事件，实现落地页 / 工作台 / 多标签实时联动。
 */
export function useTheme() {
  const [theme, setThemeState] = useState(loadTheme)
  const [soft, setSoftState] = useState(() => loadSoft(loadTheme()))

  const alwaysSoft = isAlwaysSoft(theme)
  const softOn = alwaysSoft || soft

  useEffect(() => {
    const root = document.documentElement
    root.dataset.theme = theme
    root.dataset.soft = softOn ? 'on' : 'off'
    // 天生柔主题下，模板里给不含 data-theme 的场景（如原生控件）一个色调提示
    root.style.colorScheme = ['ops', 'blueprint'].includes(theme) ? 'dark' : 'light'
    try { localStorage.setItem(LS_THEME, theme) } catch { /* 隐私模式忽略 */ }
  }, [theme, softOn])

  useEffect(() => {
    try { localStorage.setItem(LS_SOFT, soft ? 'on' : 'off') } catch { /* 隐私模式忽略 */ }
  }, [soft])

  const setTheme = useCallback((id) => {
    if (!VALID.includes(id)) return
    setThemeState(id)
    if (isAlwaysSoft(id)) setSoftState(true)
  }, [])

  const setSoft = useCallback((v) => {
    setSoftState(prev => (typeof v === 'function' ? v(prev) : v))
  }, [])

  const toggleSoft = useCallback(() => setSoftState(s => !s), [])

  /* 跨页 / 跨标签联动 */
  useEffect(() => {
    const onStorage = (e) => {
      if (e.key === LS_THEME && VALID.includes(e.newValue)) setThemeState(e.newValue)
      else if (e.key === LS_SOFT && e.newValue !== null) setSoftState(e.newValue === 'on')
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  return { theme, setTheme, soft: softOn, setSoft, toggleSoft, alwaysSoft, THEMES }
}