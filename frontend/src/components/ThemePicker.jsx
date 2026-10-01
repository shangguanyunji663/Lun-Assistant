import React, { useEffect, useRef, useState } from 'react'
import { themeFlash } from '../fx.js'

/* ============================================================
   主题选择器（顶栏）：6 主题 + 柔化开关
     · 6 主题：暗色指挥舱 / 蓝图工程 / 实验记录本 / 学术期刊 / 暖云手稿 / 晨雾有机
     · 前四个各带「锐 / 柔」两态；柔化开关只切材质与配色，不动结构
     · soft-cream / soft-mist 天生即柔，开关置灰不可用
     · v17：切换主题时以点击处为圆心播放全屏遮罩过渡，遮罩盖满瞬间换肤
   ============================================================ */
export default function ThemePicker({ theme, setTheme, soft, toggleSoft, alwaysSoft, THEMES }) {
  const [open, setOpen] = useState(false)
  const boxRef = useRef(null)

  const current = THEMES.find(t => t.id === theme) || THEMES[0]

  /* 点主题：遮罩盖满的一瞬再换肤，形成「揭幕」效果（减少动态效果环境则直接切） */
  const chooseTheme = (e, id) => {
    if (id === theme) return
    const r = e.currentTarget.getBoundingClientRect()
    themeFlash(r.left + r.width / 2, r.top + r.height / 2, () => setTheme(id))
  }

  /* 点击外部 / Esc 关闭 */
  useEffect(() => {
    if (!open) return
    const onDown = (e) => { if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false) }
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => { document.removeEventListener('mousedown', onDown); document.removeEventListener('keydown', onKey) }
  }, [open])

  return (
    <div className="theme-picker" ref={boxRef}>
      <button className="theme-trigger btn btn-ghost btn-sm" onClick={() => setOpen(o => !o)} data-magnet
              aria-expanded={open} aria-haspopup="true" title="切换主题 / 柔化">
        <span className="chip" style={{ background: current.chip }} />
        <span className="tt-label">{current.label}</span>
        <span className="tt-caret" aria-hidden="true">▾</span>
      </button>

      {open && (
        <div className="theme-pop card" role="menu">
          <div className="tp-head">
            <span className="tp-title">主题</span>
            <span className="tp-hint">只换配色与材质</span>
          </div>
          <div className="tp-grid">
            {THEMES.map(t => (
              <button key={t.id}
                      role="menuitemradio"
                      aria-checked={theme === t.id}
                      className={`tp-item${theme === t.id ? ' on' : ''}`}
                      title={t.label}
                      data-burst
                      onClick={(e) => chooseTheme(e, t.id)}>
                <span className="chip" style={{ background: t.chip }} />
                <span className="tp-name">{t.label}</span>
                {theme === t.id && <span className="tp-check" aria-hidden="true">✓</span>}
              </button>
            ))}
          </div>

          <div className="tp-sep" />

          <button className={`tp-soft${soft ? ' on' : ''}`} onClick={toggleSoft}
                  disabled={alwaysSoft}
                  title={alwaysSoft ? '该主题天生为柔化形态' : '切换圆角 / 描边 / 阴影等材质'}>
            <span className="tp-soft-track" aria-hidden="true"><i /></span>
            <span className="tp-soft-text">
              柔化材质
              <em>{alwaysSoft ? '该主题天生柔化' : (soft ? '已开启' : '已关闭')}</em>
            </span>
          </button>
        </div>
      )}
    </div>
  )
}
