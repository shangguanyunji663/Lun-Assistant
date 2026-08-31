import React, { useEffect, useRef, useState } from 'react'
import { api, sse } from './api.js'

/* ---------------- 登录页 ---------------- */
function AuthPage({ onLogin }) {
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setErr('')
    try {
      if (mode === 'login') {
        const data = await api.login(username, password)
        localStorage.setItem('lj_token', data.access_token)
        onLogin(data.user)
      } else {
        await api.register(username, password)
        const data = await api.login(username, password)
        localStorage.setItem('lj_token', data.access_token)
        onLogin(data.user)
      }
    } catch (e2) { setErr(String(e2.message || e2)) } finally { setBusy(false) }
  }

  return (
    <div className="auth-wrap">
      <form className="auth-card" onSubmit={submit}>
        <h1>论匠</h1>
        <p className="muted">LangGraph 多智能体论文全流程助手</p>
        <input placeholder="用户名（3-32位）" value={username} onChange={e => setUsername(e.target.value)} />
        <input placeholder="密码（6位以上）" type="password" value={password} onChange={e => setPassword(e.target.value)} />
        <button disabled={busy || !username || !password}>{mode === 'login' ? '登录' : '注册并登录'}</button>
        <a className="muted link" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
          {mode === 'login' ? '没有账号？去注册' : '已有账号？去登录'}
        </a>
        {err && <div className="err">{err}</div>}
      </form>
    </div>
  )
}

/* ---------------- 事件时间线 ---------------- */
const NODE_TITLES = { supervisor: '主控Agent', topic_agent: '选题Agent', literature_agent: '文献Agent', writer_agent: '写作Agent', format_agent: '格式Agent', plagiarism_agent: '查重Agent', defense_agent: '答辩Agent' }
function Timeline({ events }) {
  if (!events.length) return null
  return (
    <div className="timeline">
      {events.map((ev, i) => (
        <div key={i} className={`tl-item tl-${ev.type}`}>
          {ev.type === 'node_start' && <span className="tl-tag start">? {NODE_TITLES[ev.payload?.agent] || ev.payload?.agent || 'Agent'}</span>}
          {ev.type === 'intent' && <span className="tl-tag intent">意图: {ev.payload?.label} ({ev.payload?.layer}, conf={ev.payload?.confidence})</span>}
          {ev.type === 'route' && <span className="tl-tag route">→ 路由至 {ev.payload?.next}</span>}
          {ev.type === 'tool' && <span className="tl-tag tool">? {ev.payload?.name}</span>}
          {ev.type === 'node_end' && <span className="tl-tag end">? {ev.payload?.agent || ev.node || ''} 完成{ev.payload?.stop_reason === 'max_hops' ? '（达到最大跳数）' : ''}</span>}
          {ev.type === 'interrupt' && <span className="tl-tag interrupt">? 需要确认: {ev.payload?.question || JSON.stringify(ev.payload)}</span>}
          {ev.type === 'error' && <span className="tl-tag err">? {ev.payload?.message}</span>}
        </div>
      ))}
    </div>
  )
}

/* ---------------- Trace 面板 ---------------- */
function TracePanel() {
  const [traces, setTraces] = useState([])
  const [detail, setDetail] = useState(null)
  const [err, setErr] = useState('')

  const load = async () => {
    try { setTraces((await api.traces(30)).items) } catch (e) { setErr(String(e.message || e)) }
  }
  useEffect(() => { load() }, [])

  const open = async (id) => {
    try { setDetail(await api.trace(id)) } catch (e) { setErr(String(e.message || e)) }
  }

  return (
    <div className="trace-panel">
      <div className="trace-list">
        <div className="panel-head">
          <h3>Trace 列表</h3>
          <button onClick={load}>刷新</button>
        </div>
        {err && <div className="err">{err}</div>}
        {traces.map(t => (
          <div key={t.trace_id} className={`trace-item ${detail?.trace_id === t.trace_id ? 'active' : ''}`} onClick={() => open(t.trace_id)}>
            <div className="tid">{t.trace_id.slice(0, 12)}…</div>
            <div className="meta">{t.spans} spans · {t.total_latency_ms}ms · ${t.total_cost_usd.toFixed(6)}</div>
          </div>
        ))}
        {!traces.length && <p className="muted">暂无 Trace</p>}
      </div>
      <div className="trace-detail">
        {detail ? (
          <>
            <div className="panel-head">
              <h3>行为回放 · {detail.trace_id.slice(0, 12)}…</h3>
              <span className="muted">{detail.summary.span_count} spans · {detail.summary.total_latency_ms}ms · errors={detail.summary.error_count}</span>
            </div>
            {renderTree(detail.tree, 0)}
            <h4>时间序列</h4>
            <div className="seq">
              {detail.spans.map((s, i) => (
                <div key={i} className={`seq-row ${s.status !== 'ok' ? 'bad' : ''}`}>
                  <span className="kind">{s.kind}</span>
                  <span className="name">{s.name}</span>
                  <span className="lat">{s.latency_ms}ms</span>
                  {s.error && <span className="err-inline">{s.error}</span>}
                </div>
              ))}
            </div>
          </>
        ) : <p className="muted">选择左侧 Trace 查看回放</p>}
      </div>
    </div>
  )
}

function renderTree(nodes, depth) {
  return nodes.map((n, i) => (
    <div key={i}>
      <div className="tree-row" style={{ paddingLeft: depth * 18 }}>
        <span className={`tree-kind ${n.status !== 'ok' ? 'bad' : ''}`}>{n.kind}</span>
        {n.name}
        <span className="lat"> {n.latency_ms}ms</span>
        {n.tokens_out > 0 && <span className="muted"> · out={n.tokens_out}tok</span>}
      </div>
      {n.children?.length ? renderTree(n.children, depth + 1) : null}
    </div>
  ))
}

/* ---------------- 主应用 ---------------- */
export default function App() {
  const [user, setUser] = useState(null)
  const [booting, setBooting] = useState(true)
  const [tab, setTab] = useState('chat')
  const [projects, setProjects] = useState([])
  const [projectId, setProjectId] = useState(null)
  const sessionIdRef = useRef(null)

  // 对话状态
  const [messages, setMessages] = useState([])       // {role:'user'|'assistant', content}
  const [timeline, setTimeline] = useState([])
  const [streaming, setStreaming] = useState(false)
  const [interrupt, setInterrupt] = useState(null)   // {question, options?}
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    const t = localStorage.getItem('lj_token')
    if (!t) { setBooting(false); return }
    api.me().then(u => setUser(u)).catch(() => localStorage.removeItem('lj_token')).finally(() => setBooting(false))
  }, [])

  useEffect(() => {
    if (user) api.projects().then(ps => setProjects(ps)).catch(() => {})
  }, [user])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, timeline])

  if (booting) return <div className="center muted">加载中…</div>
  if (!user) return <AuthPage onLogin={setUser} />

  const newSession = () => {
    sessionIdRef.current = `web-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
    setMessages([]); setTimeline([]); setInterrupt(null)
  }
  if (!sessionIdRef.current) newSession()

  const send = async (text, resume = null) => {
    if (streaming) return
    setStreaming(true)
    if (!resume) {
      setMessages(m => [...m, { role: 'user', content: text }])
      setInput('')
    } else {
      setMessages(m => [...m, { role: 'user', content: `[确认反馈] ${resume}` }])
    }
    setInterrupt(null)
    let acc = ''
    setMessages(m => [...m, { role: 'assistant', content: '' }])
    const patchLast = (content) => setMessages(m => { const c = [...m]; c[c.length - 1] = { role: 'assistant', content }; return c })

    try {
      const finalText = await sse(resume ? '/agent/resume' : '/agent/chat',
        resume
          ? { session_id: sessionIdRef.current, feedback: resume, project_id: projectId }
          : { session_id: sessionIdRef.current, message: text, project_id: projectId },
        (type, payload, node) => {
          if (type === 'token') { acc += payload || ''; patchLast(acc) }
          else if (type === 'final') { if (payload?.output) patchLast(payload.output) }
          else if (type === 'interrupt') {
            setInterrupt(payload)
            setTimeline(t => [...t, { type: 'interrupt', payload, node }])
          } else if (type === 'error') {
            setTimeline(t => [...t, { type: 'error', payload, node }])
          } else if (['node_start', 'node_end', 'intent', 'route', 'tool'].includes(type)) {
            setTimeline(t => [...t, { type, payload, node }])
          }
        })
      if (finalText) patchLast(finalText)
    } catch (e) {
      patchLast(`请求失败：${e.message || e}`)
    } finally { setStreaming(false) }
  }

  const addProject = async () => {
    const title = prompt('论文题目：')
    if (!title) return
    const p = await api.createProject(title, '', '')
    setProjects(ps => [p, ...ps])
    setProjectId(p.id)
  }

  return (
    <div className="app">
      <header>
        <h1>论匠 <small>多智能体论文助手</small></h1>
        <div className="spacer" />
        <select value={projectId ?? ''} onChange={e => setProjectId(e.target.value ? Number(e.target.value) : null)}>
          <option value="">（未关联项目）</option>
          {projects.map(p => <option key={p.id} value={p.id}>{`#${p.id} ${p.title}`}</option>)}
        </select>
        <button onClick={addProject}>+ 新建项目</button>
        <button onClick={newSession} disabled={streaming}>新会话</button>
        <nav>
          <button className={tab === 'chat' ? 'on' : ''} onClick={() => setTab('chat')}>对话</button>
          <button className={tab === 'trace' ? 'on' : ''} onClick={() => setTab('trace')}>可观测</button>
        </nav>
        <span className="muted">{user.username}({user.role})</span>
        <button onClick={() => { localStorage.removeItem('lj_token'); setUser(null) }}>退出</button>
      </header>

      {tab === 'chat' ? (
        <main className="chat-layout">
          <section className="chat-col">
            <div className="messages">
              {messages.map((m, i) => (
                <div key={i} className={`msg ${m.role}`}>
                  <div className="bubble">{m.content || (streaming && i === messages.length - 1 ? '…' : '')}</div>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>
            {interrupt && (
              <div className="interrupt-bar">
                <span>? {interrupt.question || 'Agent 需要你的确认'}</span>
                {(interrupt.options || []).map(op => (
                  <button key={op} onClick={() => send(op, op)} disabled={streaming}>{op}</button>
                ))}
                <div className="free-form">
                  <input placeholder="输入你的反馈…" value={input}
                         onChange={e => setInput(e.target.value)}
                         onKeyDown={e => e.key === 'Enter' && input && send(input, input)} />
                  <button onClick={() => input && send(input, input)} disabled={streaming || !input}>发送反馈</button>
                </div>
              </div>
            )}
            <div className="input-bar">
              <textarea rows={2} placeholder="输入论文相关请求，如：帮我找几篇大模型文献 / 帮我写摘要…" value={input}
                        disabled={streaming || !!interrupt}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && input.trim()) { e.preventDefault(); send(input.trim()) } }} />
              <button className="send" disabled={streaming || !input.trim() || interrupt} onClick={() => send(input.trim())}>
                {streaming ? '生成中…' : '发送'}
              </button>
            </div>
          </section>
          <aside className="timeline-col">
            <h3>Agent 执行时间线</h3>
            <Timeline events={timeline} />
            {!timeline.length && <p className="muted">发起对话后，这里展示主控调度 / 意图识别 / 路由与工具事件</p>}
          </aside>
        </main>
      ) : (
        <main className="trace-main"><TracePanel /></main>
      )}
    </div>
  )
}
