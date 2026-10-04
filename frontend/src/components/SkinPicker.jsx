import { useEffect, useRef, useState } from 'react'

import { skinFlash } from '../fx.js'

/* ============================================================
   皮肤选择器（顶栏）· v18
     · 6 套设计语言：铅字印刷 / 夜航仪表 / 学术海报 / 木牍竖排 / 孔版双色 / 索引档案
     · 每套皮肤是「一整套设计语言」——配色、字体、排版、材质、动效性格全换，
       不是 v16 那种「同一套结构换配色」的主题。
     · 切换时以点击处为圆心播放全屏遮罩过渡，遮罩盖满的一瞬再换肤（揭幕感）。
     · 弹层底部另给一条「在落地页查看该皮肤」的入口：落地页每套皮肤一个独立
       HTML（六种版式差异过大，无法靠 CSS 换肤），所以这里是跳转而非切换。
   ============================================================ */
export default function SkinPicker({ skin, setSkin, skins }) {
  const [open, setOpen] = useState(false)
  const boxRef = useRef(null)

  const current = skins.find(s => s.id === skin) || skins[0]

  const choose = (e, id) => {
    if (id === skin) return
    const r = e.currentTarget.getBoundingClientRect()
    skinFlash(r.left + r.width / 2, r.top + r.height / 2, () => setSkin(id))
    setOpen(false)
  }

  /* 点击外部 / Esc 关闭 */
  useEffect(() => {
    if (!open) return
    const onDown = (e) => { if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false) }
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <div className="skin-picker" ref={boxRef}>
      <button className="wb-btn wb-btn-ghost skin-trigger" data-magnet
              onClick={() => setOpen(o => !o)}
              aria-expanded={open} aria-haspopup="true"
              title="切换设计语言（整套视觉，非仅配色）">
        <span className="sp-chip" style={{ background: current.chip }} aria-hidden="true" />
        <span className="sp-label">{current.label}</span>
        <span className="sp-caret" aria-hidden="true">▾</span>
      </button>

      {open && (
        <div className="skin-pop" role="menu">
          <div className="sp-head">
            <span className="sp-title">设计语言</span>
            <span className="sp-hint">整套视觉 · {skins.length} 选 1</span>
          </div>

          <div className="sp-grid">
            {skins.map(s => (
              <button key={s.id}
                      role="menuitemradio"
                      aria-checked={skin === s.id}
                      className={`sp-item${skin === s.id ? ' on' : ''}`}
                      data-burst
                      onClick={(e) => choose(e, s.id)}>
                <span className="sp-chip" style={{ background: s.chip }} aria-hidden="true" />
                <span className="sp-body">
                  <span className="sp-name">{s.label}<em>{s.en}</em></span>
                  <span className="sp-desc">{s.desc}</span>
                </span>
                {skin === s.id && <span className="sp-check" aria-hidden="true">✓</span>}
              </button>
            ))}
          </div>

          <a className="sp-foot" href={current.landing}>
            在落地页查看「{current.label}」→
          </a>
        </div>
      )}
    </div>
  )
}