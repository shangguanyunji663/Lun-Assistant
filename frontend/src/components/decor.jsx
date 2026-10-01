import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/* 印章 / 图记：可复用品牌标识。
   颜色走 CSS 变量（--accent / --accent-ink），随主题与柔化态自动变化；
   形状由 .seal 的 border-radius 控制（柔主题下接近圆形，锐主题下为方形）。 */
export function Seal({ size = 28, char = '论' }) {
  return (
    <span className="seal" style={{ width: size, height: size, fontSize: Math.round(size * 0.52) }}
          aria-hidden="true">
      <span className="seal-char">{char}</span>
    </span>
  )
}

/* 细分隔线：标题下的轻量装饰（取代旧毛笔撇） */
export function Rule({ width = 96 }) {
  return <span className="rule" style={{ width }} aria-hidden="true" />
}

/* 背景氛围：三条缓慢流动的曲线（v17 动效层；样式见 styles.css · 背景氛围动效）
   纯装饰，fixed 定位且不接收指针事件，不参与任何布局。 */
export function AmbientLines() {
  return (
    <div className="ambient-lines" aria-hidden="true">
      <svg viewBox="0 0 1440 900" preserveAspectRatio="none">
        <path className="flow-1" d="M-40 220 C 260 120, 520 340, 820 250 S 1300 120, 1480 230" />
        <path className="flow-2" d="M-40 520 C 300 430, 560 640, 900 540 S 1320 420, 1480 520" />
        <path className="flow-3" d="M-40 760 C 240 690, 600 830, 900 740 S 1340 660, 1480 750" />
      </svg>
    </div>
  )
}

/* markdown 渲染：助手消息支持标题/列表/表格/代码块 */
export function Markdown({ children }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]}
                   components={{ a: props => <a {...props} target="_blank" rel="noreferrer" /> }}>
      {children}
    </ReactMarkdown>
  )
}