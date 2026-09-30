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

/* markdown 渲染：助手消息支持标题/列表/表格/代码块 */
export function Markdown({ children }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]}
                   components={{ a: props => <a {...props} target="_blank" rel="noreferrer" /> }}>
      {children}
    </ReactMarkdown>
  )
}