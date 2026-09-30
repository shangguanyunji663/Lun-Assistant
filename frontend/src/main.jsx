import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './tokens.css'
import './styles.css'
// v16 主题装饰层：严格对齐 design-samples/proposal-1~10 样张的招牌视觉。
// 必须排在 styles.css 之后，才能覆盖同优先级的装饰规则。
import './themes/ops.css'
import './themes/blueprint.css'
import './themes/lab.css'
import './themes/press.css'
import './themes/soft.css'

ReactDOM.createRoot(document.getElementById('root')).render(<App />)
