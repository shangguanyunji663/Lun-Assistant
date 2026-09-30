import React, { useState } from 'react'
import { api } from '../api.js'
import { Seal } from './decor.jsx'
import ThemePicker from './ThemePicker.jsx'

/* ============================================================
   登录页 · 左品牌 / 右表单
     主题与柔化开关同样可用（只改材质配色，与工作台完全一致）
   ============================================================ */
export default function AuthPage({ onLogin, themeCtl }) {
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
    <div className="auth-wrap">
      {themeCtl && (
        <div className="auth-theme"><ThemePicker {...themeCtl} /></div>
      )}

      {/* 左 · 品牌区 */}
      <section className="auth-brand">
        <div className="brand-seal"><Seal size={56} /></div>
        <h1 className="brand-vert">论匠</h1>
        <p className="brand-en">LunJiang · 多智能体论文全流程助手</p>
        <ul className="brand-points">
          <li>选题 · 文献 · 写作 · 格式 · 查重 · 答辩</li>
          <li>主控智能体调度，产出经你确认后落稿</li>
          <li>全链路留痕，执行过程可回放</li>
        </ul>
      </section>

      {/* 右 · 表单区 */}
      <form className="auth-card card" onSubmit={submit}>
        <h2>{isLogin ? '登录' : '注册'}</h2>
        <p className="muted">{isLogin ? '登录以继续使用' : '注册后将自动登录'}</p>

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

        <button className="btn btn-ink auth-submit" disabled={busy || !username || !password}>
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
