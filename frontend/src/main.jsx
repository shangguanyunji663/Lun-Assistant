import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'

/* 样式加载顺序（唯一真源，勿随意调整）：
   base.css    → 与皮肤无关的结构性样式（重置 / 焦点 / 弹窗骨架 / markdown 结构）
   panels.css  → 共享组件层（知识库 / 档案 / 可观测 / 登录页），只吃皮肤令牌变量
   fx.css      → v17 动效层（入场编排 / 指针特效 / 氛围 / 高光时刻）
   skins/*     → 8 套设计语言，按 [data-skin] 作用域各自生效；
                 放最后，才能覆盖 base / panels / fx 里的同优先级声明。
   注：8 份皮肤 CSS 全量引入（每份约 5–8KB gzip）而非按需动态加载——
       避免切换时异步拉取造成的白帧；总量可控，换取切换零延迟。 */
import './styles/base.css'
import './styles/panels.css'
import './fx.css'
import './skins/a-letterpress.css'
import './skins/b-console.css'
import './skins/c-poster.css'
import './skins/d-bamboo.css'
import './skins/e-riso.css'
import './skins/f-archive.css'
import './skins/g-score.css'
import './skins/h-contact.css'
/* 工作台外壳与滚动契约：必须放在 skins/*.css 之后——
   各皮肤都把 .wb 写成 min-height:100vh，本文件负责收敛为视口高度 + 区内滚动 */
import './styles/layout.css'

ReactDOM.createRoot(document.getElementById('root')).render(<App />)