import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/* 朱砂钤印：可复用视觉标识（极小面积强调色，不用作常规按钮色） */
export function Seal({ size = 28, char = '论' }) {
  return (
    <svg className="seal" width={size} height={size} viewBox="0 0 40 40" aria-hidden="true">
      <rect x="2" y="2" width="36" height="36" rx="3" fill="#9E3B2C" />
      <rect x="5" y="5" width="30" height="30" rx="2" fill="none" stroke="#F6F3EC" strokeWidth="1.2" opacity="0.72" />
      <text x="20" y="27" textAnchor="middle" fill="#F6F3EC" fontSize="20"
            fontFamily="STKaiti, KaiTi, 楷体, serif" fontWeight="600">{char}</text>
    </svg>
  )
}

/* 毛笔一撇：标题下的墨迹分隔 */
export function BrushRule({ width = 96 }) {
  return (
    <svg className="brush-rule" width={width} height="6" viewBox="0 0 96 6" aria-hidden="true">
      <path d="M1 4.2 C 22 1.6 44 1.4 62 2.4 C 76 3.1 88 4.0 95 4.8"
            stroke="currentColor" strokeWidth="2.4" fill="none"
            strokeLinecap="round" opacity="0.5" />
    </svg>
  )
}

/* 卷轴木轴：上下两道赭石金，营造装裱感（固定在视口上下沿） */
export function WoodRoll() {
  return (
    <>
      <div className="wood-roll top" />
      <div className="wood-roll bot" />
    </>
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
