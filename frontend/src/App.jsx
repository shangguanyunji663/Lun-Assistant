import React, { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api, sse } from './api.js'

/* markdown ??????????????????/?б?/????/????? */
function Markdown({ children }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]}
                   components={{
                     a: props => <a {...props} target="_blank" rel="noreferrer" />,
                   }}>
      {children}
    </ReactMarkdown>
  )
}

/* ---------------- ???? ---------------- */
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
        <h1>???</h1>
        <p className="muted">LangGraph ?????????????????????</p>
        <input placeholder="???????3-32λ??" value={username} onChange={e => setUsername(e.target.value)} />
        <input placeholder="????6λ?????" type="password" value={password} onChange={e => setPassword(e.target.value)} />
        <button disabled={busy || !username || !password}>{mode === 'login' ? '???' : '??????'}</button>
        <a className="muted link" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
          {mode === 'login' ? '???????????' : '????????????'}
        </a>
        {err && <div className="err">{err}</div>}
      </form>
    </div>
  )
}

/* ---------------- ???????? ---------------- */
const NODE_TITLES = { supervisor: '????Agent', topic_agent: '???Agent', literature_agent: '????Agent', writer_agent: 'д??Agent', format_agent: '???Agent', plagiarism_agent: '????Agent', defense_agent: '???Agent' }
function Timeline({ events }) {
  if (!events.length) return null
  return (
    <div className="timeline">
      {events.map((ev, i) => (
        <div key={i} className={`tl-item tl-${ev.type}`}>
          {ev.type === 'node_start' && <span className="tl-tag start">? {NODE_TITLES[ev.payload?.agent] || ev.payload?.agent || 'Agent'}</span>}
          {ev.type === 'intent' && <span className="tl-tag intent">???: {ev.payload?.label} ({ev.payload?.layer}, conf={ev.payload?.confidence})</span>}
          {ev.type === 'route' && <span className="tl-tag route">?? ·???? {ev.payload?.next}</span>}
          {ev.type === 'tool' && <span className="tl-tag tool">? {ev.payload?.name}</span>}
          {ev.type === 'node_end' && <span className="tl-tag end">? {ev.payload?.agent || ev.node || ''} ???{ev.payload?.stop_reason === 'max_hops' ? '?????????????' : ''}</span>}
          {ev.type === 'interrupt' && <span className="tl-tag interrupt">? ??????: {ev.payload?.question || JSON.stringify(ev.payload)}</span>}
          {ev.type === 'error' && <span className="tl-tag err">? {ev.payload?.message}</span>}
        </div>
      ))}
    </div>
  )
}

/* ---------------- Trace ??? ---------------- */
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
          <h3>Trace ?б?</h3>
          <button onClick={load}>???</button>
        </div>
        {err && <div className="err">{err}</div>}
        {traces.map(t => (
          <div key={t.trace_id} className={`trace-item ${detail?.trace_id === t.trace_id ? 'active' : ''}`} onClick={() => open(t.trace_id)}>
            <div className="tid">{t.trace_id.slice(0, 12)}??</div>
            <div className="meta">{t.spans} spans ?? {t.total_latency_ms}ms ?? ${t.total_cost_usd.toFixed(6)}</div>
          </div>
        ))}
        {!traces.length && <p className="muted">???? Trace</p>}
      </div>
      <div className="trace-detail">
        {detail ? (
          <>
            <div className="panel-head">
              <h3>?????? ?? {detail.trace_id.slice(0, 12)}??</h3>
              <span className="muted">{detail.summary.span_count} spans ?? {detail.summary.total_latency_ms}ms ?? errors={detail.summary.error_count}</span>
            </div>
            {renderTree(detail.tree, 0)}
            <h4>???????</h4>
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
        ) : <p className="muted">?????? Trace ?????</p>}
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
        {n.tokens_out > 0 && <span className="muted"> ?? out={n.tokens_out}tok</span>}
      </div>
      {n.children?.length ? renderTree(n.children, depth + 1) : null}
    </div>
  ))
}

/* ---------------- ????? ---------------- */
export default function App() {
  const [user, setUser] = useState(null)
  const [booting, setBooting] = useState(true)
  const [tab, setTab] = useState('chat')
  const [projects, setProjects] = useState([])
  const [projectId, setProjectId] = useState(null)
  const sessionIdRef = useRef(null)

  // ?????
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

  if (booting) return <div className="center muted">?????С?</div>
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
      setMessages(m => [...m, { role: 'user', content: `[??????] ${resume}` }])
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
      patchLast(`????????${e.message || e}`)
    } finally { setStreaming(false) }
  }

  const addProject = async () => {
    const title = prompt('?????????')
    if (!title) return
    const p = await api.createProject(title, '', '')
    setProjects(ps => [p, ...ps])
    setProjectId(p.id)
  }

  return (
    <div className="app">
      <header>
        <h1>??? <small>????????????????</small></h1>
        <div className="spacer" />
        <select value={projectId ?? ''} onChange={e => setProjectId(e.target.value ? Number(e.target.value) : null)}>
          <option value="">??δ?????????</option>
          {projects.map(p => <option key={p.id} value={p.id}>{`#${p.id} ${p.title}`}</option>)}
        </select>
        <button onClick={addProject}>+ ??????</button>
        <button onClick={newSession} disabled={streaming}>???</button>
        <nav>
          <button className={tab === 'chat' ? 'on' : ''} onClick={() => setTab('chat')}>???</button>
          <button className={tab === 'trace' ? 'on' : ''} onClick={() => setTab('trace')}>????</button>
        </nav>
        <span className="muted">{user.username}({user.role})</span>
        <button onClick={() => { localStorage.removeItem('lj_token'); setUser(null) }}>???</button>
      </header>

      {tab === 'chat' ? (
        <main className="chat-layout">
          <section className="chat-col">
            <div className="messages">
              {messages.map((m, i) => (
                <div key={i} className={`msg ${m.role}`}>
                  <div className="bubble">
                    {m.role === 'assistant' ? <Markdown>{m.content || (streaming && i === messages.length - 1 ? '??' : '')}</Markdown> : m.content}
                  </div>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>
            {interrupt && (
              <div className="interrupt-bar">
                <span>? {interrupt.question || 'Agent ?????????'}</span>
                {(interrupt.options || []).map(op => (
                  <button key={op} onClick={() => send(op, op)} disabled={streaming}>{op}</button>
                ))}
                <div className="free-form">
                  <input placeholder="????????????" value={input}
                         onChange={e => setInput(e.target.value)}
                         onKeyDown={e => e.key === 'Enter' && input && send(input, input)} />
                  <button onClick={() => input && send(input, input)} disabled={streaming || !input}>???????</button>
                </div>
              </div>
            )}
            <div className="input-bar">
              <textarea rows={2} placeholder="????????????????磺????????????????? / ????д????" value={input}
                        disabled={streaming || !!interrupt}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && input.trim()) { e.preventDefault(); send(input.trim()) } }} />
              <button className="send" disabled={streaming || !input.trim() || interrupt} onClick={() => send(input.trim())}>
                {streaming ? '?????С?' : '????'}
              </button>
            </div>
          </section>
          <aside className="timeline-col">
            <h3>Agent ????????</h3>
            <Timeline events={timeline} />
            {!timeline.length && <p className="muted">????????????????????? / ?????? / ·?????????</p>}
          </aside>
        </main>
      ) : (
        <main className="trace-main"><TracePanel /></main>
      )}
    </div>
  )
}
