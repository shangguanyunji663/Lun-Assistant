import React from 'react'

/* ============================================================
   背景层 · 青绿长卷（放松版）

   分层（由底至顶）：
     1. ink-photo  AI 山水底图     opacity 0.16（硬上限，登录页 0.22）
     2. ink-veil   二次压制渐变     上淡下浓，文字区有效 ≤0.06
     3. ink-wash   墨滴晕染        周期 120~150s，幅度 ≤1.2vw
     4. paper-grain 宣纸纤维        opacity 0.045

   透明度预算（顶部 → 底部，普通页）：
      0%  →  0.16 × (1 - 0.28) = 0.115
     26%  →  0.16 × (1 - 0.62) = 0.061
     50%  →  0.16 × (1 - 0.88) = 0.019
    100%  →  0.16 × (1 - 1.00) = 0.000
   即内容区近乎纯色底，图只存在于余光里，不与文字争对比度。
   ============================================================ */
export default function InkBackground({ dense = false }) {
  return (
    <div className="ink-bg" aria-hidden="true">
      {/* 1 · AI 山水底图 */}
      <div className={`ink-photo${dense ? ' dense' : ''}`} />

      {/* 2 · 压制层 */}
      <div className="ink-veil" />

      {/* 3 · 墨滴晕染（极缓，几乎察觉不到） */}
      <div className="ink-wash">
        <span className="ink-blob ink-blob-1" />
        <span className="ink-blob ink-blob-2" />
      </div>

      {/* 4 · 宣纸纤维 */}
      <svg className="paper-grain">
        <filter id="lj-grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.82" numOctaves="3" stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#lj-grain)" />
      </svg>

      {/* 5 · B 主题装饰 · 册页中缝（左中 1px 灰色宣纸分隔线；A/C 主题隐藏） */}
      <div className="ink-divider" />

      {/* 6 · C 主题装饰 · 钤印（右下角 38×38 红边框"匠"字章；A/B 主题隐藏） */}
      <div className="ink-stamp">匠</div>
    </div>
  )
}
