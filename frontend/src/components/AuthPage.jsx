import React, { useState } from 'react'
import { api } from '../api.js'
import InkBackground from '../InkBackground.jsx'
import { Seal, BrushRule, WoodRoll } from './decor.jsx'

/* ============================================================
   登录页 · 三分构图
     左：品牌区（竖排题款 + 钤印）  —— 留白定调，不着一字于表单
     中：册页中缝（一道赭金竖线）  —— 分隔并引导视线
     右：表单区（玻璃册页卡）       —— 全页唯一行动区
   ============================================================ */
export default function AuthPage({ onLogin }) {
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
      <InkBackground dense />
      <WoodRoll />

      {/* 左 · 品牌区 */}
      <div className="auth-brand">
        <div className="brand-vert">论匠</div>
        <div className="brand-en">多智能体 · 论文全流程助手</div>
        <div className="brand-seal"><Seal size={54} /></div>
      </div>

      {/* 中 · 册页中缝 */}
      <div className="auth-split" />

      {/* 右 · 表单区 */}
      <form className="auth-card" onSubmit={submit}>
        <h1>{isLogin ? '登 录' : '注 册'}</h1>
        <div className="auth-rule"><BrushRule width={120} /></div>
        <p className="muted">{isLogin ? '登录以继续使用' : '注册后将自动登录'}</p>

        <input placeholder="用户名（3-32位）" value={username}
               onChange={e => setUsername(e.target.value)} autoComplete="username" />
        <input placeholder="密码（6位以上）" type="password" value={password}
               onChange={e => setPassword(e.target.value)}
               autoComplete={isLogin ? 'current-password' : 'new-password'} />

        <button disabled={busy || !username || !password}>
          {busy ? '处理中…' : (isLogin ? '登 录' : '注册并登录')}
        </button>

        <a className="muted link" onClick={() => setMode(isLogin ? 'register' : 'login')}>
          {isLogin ? '尚无账号 · 注册' : '已有账号 · 登录'}
        </a>

        {err && <div className="err">{err}</div>}
      </form>

      <p className="auth-foot">选题 · 文献 · 写作 · 格式 · 查重 · 答辩</p>
    </div>
  )
}
