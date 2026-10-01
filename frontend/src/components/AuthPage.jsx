import { useState } from 'react'

import { api } from '../api.js'
import { Seal } from './decor.jsx'
import SkinPicker from './SkinPicker.jsx'

/* ============================================================
   登录页 · 左品牌 / 右表单
     皮肤（6 套设计语言）在此同样可切换，切换即时生效——
     登录页与工作台共用同一套 .wb-* / .auth-* 皮肤样式。
   ============================================================ */
export default function AuthPage({ onLogin, skinCtl }) {
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setErr('')
    try {
      if (mode === 'register') await api.register(username, password)
      const data = await api.login(username, password)
      localStorage.setItem('lj_token', data.access_token)
      onLogin(data.user)
    } catch (e2) { setErr(String(e2.message || e2)) } finally { setBusy(false) }
  }

  const isLogin = mode === 'login'

  return (
    <div className="auth">
      {skinCtl && (
        <div className="auth-skin"><SkinPicker {...skinCtl} /></div>
      )}

      {/* 左 · 品牌区 */}
      <section className="auth-brand">
        <Seal size={56} />
        <h1 className="auth-title">论匠</h1>
        <p className="auth-sub">LunJiang · 多智能体论文全流程助手</p>
        <ul className="auth-points">
          <li>选题 · 文献 · 写作 · 格式 · 查重 · 答辩</li>
          <li>主控智能体调度，产出经你确认后落稿</li>
          <li>全链路留痕，执行过程可回放</li>
        </ul>
      </section>

      {/* 右 · 表单区 */}
      <form className="auth-card" onSubmit={submit}>
        <h2>{isLogin ? '登录' : '注册'}</h2>
        <p className="auth-note muted">{isLogin ? '登录以继续使用' : '注册后将自动登录'}</p>

        <label className="field">
          <span>用户名</span>
          <input placeholder="3–32 位" value={username}
                 onChange={e => setUsername(e.target.value)} autoComplete="username" />
        </label>
        <label className="field">
          <span>密码</span>
          <input placeholder="6 位以上" type="password" value={password}
                 onChange={e => setPassword(e.target.value)}
                 autoComplete={isLogin ? 'current-password' : 'new-password'} />
        </label>

        <button className="wb-btn wb-btn-ink auth-submit" data-magnet
                disabled={busy || !username || !password}>
          {busy ? '处理中…' : (isLogin ? '登 录' : '注册并登录')}
        </button>

        <div className="auth-links">
          <a className="link" onClick={() => setMode(isLogin ? 'register' : 'login')}>
            {isLogin ? '尚无账号 · 注册' : '已有账号 · 登录'}
          </a>
          <a className="link" href="./">← 返回首页</a>
        </div>

        {err && <div className="err">{err}</div>}
      </form>
    </div>
  )
}