import React, { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api, sse } from './api.js'

/* markdown 渲染：助手消息支持标题/列表/表格/代码块 */
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
const NODE_TITLES = {
  supervisor: '主控Agent', topic_agent: '选题Agent', literature_agent: '文献Agent',
  writing_agent: '写作Agent', format_agent: '格式Agent', plagiarism_agent: '查重Agent',
  ai_detect_agent: 'AI检测Agent', planner: '任务规划Agent',
}
function Timeline({ events }) {
  if (!events.length) return null
  return (
    <div className="timeline">
      {events.map((ev, i) => (
        <div key={i} className={`tl-item tl-${ev.type}`}>
          {ev.type === 'node_start' && <span className="tl-tag start">▶ {NODE_TITLES[ev.payload?.agent] || ev.payload?.agent || 'Agent'}</span>}
          {ev.type === 'intent' && <span className="tl-tag intent">意图: {ev.payload?.label} ({ev.payload?.layer}, conf={ev.payload?.confidence})</span>}
          {ev.type === 'route' && <span className="tl-tag route">→ 路由至 {ev.payload?.next}</span>}
          {ev.type === 'tool' && <span className="tl-tag tool">🔧 {ev.payload?.name}</span>}
          {ev.type === 'plan' && <span className="tl-tag plan">📋 规划 {ev.payload?.goal?.slice(0, 40) || ''} · {ev.payload?.steps?.length || 0} 步</span>}
          {ev.type === 'step_event' && <span className="tl-tag step">• 步骤 {ev.payload?.step}/{ev.payload?.total} {ev.payload?.action}{ev.payload?.status === 'ok' ? ' ✓' : ' ⚠'}</span>}
          {ev.type === 'node_end' && <span className="tl-tag end">✔ {NODE_TITLES[ev.payload?.agent] || ev.payload?.agent || ev.node || ''} 完成{ev.payload?.stop_reason === 'max_hops' ? '（达到最大跳数）' : ''}</span>}
          {ev.type === 'interrupt' && <span className="tl-tag interrupt">⏸ 需要确认: {ev.payload?.question || JSON.stringify(ev.payload)}</span>}
          {ev.type === 'error' && <span className="tl-tag err">✖ {ev.payload?.message}</span>}
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

/* ---------------- 项目知识库面板 ---------------- */
const FMT_ICON = { pdf: '📕', docx: '📘', txt: '📄', md: '📝' }
function StatusBadge({ status }) {
  return <span className={`kb-status kb-status-${status}`}>{status}</span>
}
function KnowledgePanel({ projectId, onNotice }) {
  const [docs, setDocs] = useState([])
  const [err, setErr] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState('')
  const [summary, setSummary] = useState(null)          // 上传汇总 {uploaded, ready, 逐文件}
  const [q, setQ] = useState('')
  const [mode, setMode] = useState('hybrid')
  const [hits, setHits] = useState(null)
  const [fallback, setFallback] = useState(false)   // 库内未命中已回退公共语料
  const [searching, setSearching] = useState(false)
  const fileRef = useRef(null)

  const load = async (pid = projectId) => {
    if (!pid) { setDocs([]); return }
    try { setDocs((await api.listKnowledge(pid)).documents); setErr('') }
    catch (e) { setErr(String(e.message || e)) }
  }
  useEffect(() => { load(); setHits(null); setUploadMsg('') }, [projectId])

  const upload = async (files) => {
    const arr = Array.from(files || [])
    if (!arr.length || uploading) return
    setUploading(true); setUploadMsg(''); setErr('')
    try {
      const r = await api.uploadKnowledge(projectId, arr)
      setSummary(r)
      setUploadMsg(r.ready > 0
        ? `已入库 ${r.ready}/${arr.length} 份` : `本次 ${arr.length} 份均未入库`)
      onNotice?.(r)
    } catch (e) { setErr(String(e.message || e)) }
    finally { setUploading(false); setHits(null); load() }
    fileRef.current && (fileRef.current.value = '')
  }

  const remove = async (docId, filename) => {
    if (!window.confirm(`确定从知识库删除「${filename}」？对应向量分块与原始文件将一并清除。`)) return
    try { await api.deleteKnowledge(projectId, docId); setErr(''); load(); setHits(null) }
    catch (e) { setErr(String(e.message || e)) }
  }

  const search = async () => {
    const query = q.trim()
    if (!query || searching) return
    setSearching(true); setErr(''); setFallback(false)
    try {
      let results = (await api.searchKnowledge(projectId, query, 5, mode)).results
      // 库内(mode=project)未命中 → 自动回退公共语料（hybrid）兜底，并提示来源
      if (mode === 'project' && !results.length) {
        results = (await api.searchKnowledge(projectId, query, 5, 'hybrid')).results
        setFallback(true)
      }
      setHits(results)
    } catch (e) { setErr(String(e.message || e)) }
    finally { setSearching(false) }
  }

  return (
    <div className="kb-panel">
      <div className="panel-head">
        <h3>项目知识库</h3>
        <button onClick={() => load()} disabled={uploading || !projectId}>刷新</button>
      </div>

      {!projectId && <p className="muted">请先在顶部选择或新建论文项目，再上传你的参考资料。</p>}

      {projectId && (<>
        <div className="kb-drop"
             onClick={() => fileRef.current?.click()}
             onDragOver={e => e.preventDefault()}
             onDrop={e => { e.preventDefault(); upload(e.dataTransfer.files) }}
             onKeyDown={e => e.key === 'Enter' && fileRef.current?.click()}
             role="button" tabIndex={0}>
          <input ref={fileRef} type="file" multiple hidden
                 accept=".pdf,.docx,.txt,.md,.markdown"
                 onChange={e => upload(e.target.files)} />
          <div className="kb-drop-icon">{uploading ? '存' : '＋'}</div>
          <div>{uploading ? '解析入库中…（分块 + 向量化）' : '点击或拖拽上传资料'}</div>
          <div className="muted">格式：PDF / DOCX / TXT / MD ｜ 单文件 ≤20MB ｜ 同内容自动去重</div>
        </div>

        {uploadMsg && (
          <div className="kb-upload-msg">
            <span>{uploadMsg}</span>
            {summary?.results?.map((r, i) => (
              <span key={i} className={`kb-mini kb-mini-${r.status}`}>
                {r.status === 'ready' ? '✓' : r.status === 'skipped' ? '＝' : '✕'} {r.filename}
              </span>
            ))}
          </div>
        )}
        {err && <div className="err">{err}</div>}

        <div className="kb-search">
          <input placeholder="库内检索：如 RRF 倒数排名融合…" value={q}
                 onChange={e => setQ(e.target.value)}
                 onKeyDown={e => { if (e.key === 'Enter') search() }} />
          <select value={mode} onChange={e => setMode(e.target.value)} title="检索范围">
            <option value="hybrid">hybrid</option>
            <option value="project">库内</option>
          </select>
          <button onClick={search} disabled={searching || !q.trim()}>{searching ? '…' : '检索'}</button>
        </div>

        {hits !== null && (
          <div className="kb-hits">
            <div className="panel-head"><h3>{hits.length ? '检索命中' : '未命中'}</h3>
              <span className="muted link" onClick={() => setHits(null)}>收起</span></div>
            {fallback && !hits.length &&
              <p className="muted">库内无命中，已自动检索公共语料（把“检索”右侧模式切回 hybrid 即可默认合并检索）。</p>}
            {fallback && hits.length > 0 &&
              <div className="kb-fallback-tip">库内未命中，已为你检索公共语料（hybrid 模式）</div>}
            {hits.map((h, i) => (
              <div key={i} className="kb-hit">
                <div className="kb-hit-head">
                  <span className="kh-src">{h.doc_id ? '📄 知识库' : '📚 公共语料'}</span>
                  <span className="kh-score">{h.score}</span>
                  {h.noise_flag !== 'ok' && <span className={`kb-mini kb-mini-${h.noise_flag === 'sparse_only' ? 'failed' : 'weak'}`}>{h.noise_flag}</span>}
                </div>
                <div className="kh-name">{h.filename || h.source || '(文档)'}</div>
                <div className="kh-content">{h.content}</div>
              </div>
            ))}
          </div>
        )}

        <div className="kb-docs">
          <div className="panel-head"><h3>资料清单 {docs.length ? `（${docs.length}）` : ''}</h3></div>
          {!docs.length && <p className="muted">还没有上传资料：把论文相关的 PDF、笔记、课件丢进来，对话检索会优先引用它们。</p>}
          {docs.map(d => (
            <div key={d.id} className={`kb-doc ${d.status !== 'ready' ? 'kb-doc-bad' : ''}`}>
              <div className="kd-icon">{FMT_ICON[d.file_type] || '📄'}</div>
              <div className="kd-body">
                <div className="kd-name" title={d.filename}>{d.filename}</div>
                <div className="kd-meta">
                  <StatusBadge status={d.status} />
                  {d.chunk_count > 0 && <span>{d.chunk_count} 分块</span>}
                  {d.word_count > 0 && <span>{d.word_count.toLocaleString()} 字</span>}
                  <span>{d.file_type}</span>
                </div>
                {d.error && <div className="kd-err">{d.error}</div>}
              </div>
              {d.status === 'ready' && (
                <button className="kd-del" title="删除"
                        onClick={() => remove(d.id, d.filename)}>✕</button>
              )}
            </div>
          ))}
        </div>
      </>)}
    </div>
  )
}

/* ---------------- 主应用 ---------------- */
export default function App() {
  const [user, setUser] = useState(null)
  const [booting, setBooting] = useState(true)
  const [tab, setTab] = useState('chat')
  const [projects, setProjects] = useState([])
  const [projectsErr, setProjectsErr] = useState('')   // 项目加载失败提示
  const [projectId, setProjectId] = useState(null)
  const [projectModalOpen, setProjectModalOpen] = useState(false)   // 新建项目弹窗（替代 prompt）
  const [projectTitle, setProjectTitle] = useState('')
  const sessionIdRef = useRef(null)

  // 对话状态
  const [messages, setMessages] = useState([])       // {role:'user'|'assistant', content}
  const [timeline, setTimeline] = useState([])
  const [streaming, setStreaming] = useState(false)
  const [interrupt, setInterrupt] = useState(null)   // {question, options?}
  const [input, setInput] = useState('')
  const [sideTab, setSideTab] = useState('timeline')   // 右栏：timeline | knowledge
  const bottomRef = useRef(null)

  useEffect(() => {
    const t = localStorage.getItem('lj_token')
    if (!t) { setBooting(false); return }
    api.me().then(u => setUser(u)).catch(e => {
      console.warn('[me] 自动登录失败:', e)
      localStorage.removeItem('lj_token')
    }).finally(() => setBooting(false))
  }, [])

  useEffect(() => {
    if (user) {
      api.projects().then(ps => { setProjects(ps); setProjectsErr('') })
        .catch(e => {
          const msg = String(e.message || e)
          setProjectsErr(msg)
          console.warn('[projects] 加载失败:', msg)
        })
    }
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
          } else if (['node_start', 'node_end', 'intent', 'route', 'tool', 'plan', 'step_event'].includes(type)) {
            setTimeline(t => [...t, { type, payload, node }])
          }
        })
      if (finalText) patchLast(finalText)
    } catch (e) {
      const msg = `请求失败：${e.message || e}`
      patchLast(msg)
      console.warn('[chat]', msg, e)
    } finally { setStreaming(false) }
  }

  // 打开新建项目弹窗
  const openAddProject = () => { setProjectTitle(''); setProjectModalOpen(true) }
  const confirmAddProject = async () => {
    const title = projectTitle.trim()
    if (!title) return
    try {
      const p = await api.createProject(title, '', '')
      setProjects(ps => [p, ...ps])
      setProjectId(p.id)
      setProjectModalOpen(false)
      setProjectsErr('')
    } catch (e) {
      const msg = String(e.message || e)
      setProjectsErr(`新建项目失败：${msg}`)
      console.warn('[createProject]', msg)
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1 className="brand">论匠<small>多智能体论文全流程助手</small></h1>
        <div className="spacer" />
        <select value={projectId ?? ''} onChange={e => setProjectId(e.target.value ? Number(e.target.value) : null)}>
          <option value="">（未关联项目）</option>
          {projects.map(p => <option key={p.id} value={p.id}>{`#${p.id} ${p.title}`}</option>)}
        </select>
        <button onClick={openAddProject}>+ 新建项目</button>
        <button onClick={newSession} disabled={streaming}>新会话</button>
        <nav>
          <button className={tab === 'chat' ? 'on' : ''} onClick={() => setTab('chat')}>对话</button>
          <button className={tab === 'trace' ? 'on' : ''} onClick={() => setTab('trace')} title={user.role !== 'admin' ? '仅 admin 可见 Trace 数据' : ''}>可观测</button>
        </nav>
        <span className="muted">{user.username}({user.role})</span>
        <button onClick={() => { localStorage.removeItem('lj_token'); setUser(null) }}>退出</button>
      </header>

      {projectsErr && <div className="top-banner err">{projectsErr} <span className="link" onClick={() => setProjectsErr('')}>×</span></div>}
      {user.role !== 'admin' && tab === 'trace' && (
        <div className="top-banner warn">⚠ 当前账号是 {user.role}，Trace 列表需要 admin 权限；此页面将无法加载数据。</div>
      )}

      {/* 新建项目弹窗（替代原生 prompt，避免被拦截） */}
      {projectModalOpen && (
        <div className="modal-mask" onClick={e => { if (e.target === e.currentTarget) setProjectModalOpen(false) }}>
          <div className="modal-card" onClick={e => e.stopPropagation()}>
            <h3>新建论文项目</h3>
            <p className="muted">先给你的论文起一个题目，后续可以随时修改。</p>
            <input autoFocus placeholder="例如：基于 LangGraph 的多智能体论文助手" value={projectTitle}
                   style={{ width: '100%' }}
                   onChange={e => setProjectTitle(e.target.value)}
                   onKeyDown={e => { if (e.key === 'Enter' && projectTitle.trim()) confirmAddProject() }} />
            <div className="modal-actions">
              <button onClick={() => setProjectModalOpen(false)}>取消</button>
              <button className="primary" onClick={confirmAddProject} disabled={!projectTitle.trim()}>确定</button>
            </div>
          </div>
        </div>
      )}

      {tab === 'chat' ? (
        <main className="chat-layout">
          <section className="chat-col">
            <div className="messages">
              {messages.map((m, i) => (
                <div key={i} className={`msg ${m.role}`}>
                  <div className="bubble">
                    {m.role === 'assistant' ? <Markdown>{m.content || (streaming && i === messages.length - 1 ? '…' : '')}</Markdown> : m.content}
                  </div>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>
            {interrupt && (
              <div className="interrupt-bar">
                <span>⏸ {interrupt.question || 'Agent 需要你的确认'}</span>
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
          <aside className="side-col">
            <div className="side-tabs">
              <button className={sideTab === 'timeline' ? 'on' : ''} onClick={() => setSideTab('timeline')}>执行时间线</button>
              <button className={sideTab === 'knowledge' ? 'on' : ''} onClick={() => setSideTab('knowledge')}>项目知识库</button>
            </div>
            {sideTab === 'timeline' ? (
              <div className="side-scroll">
                <Timeline events={timeline} />
                {!timeline.length &&
                  <p className="muted">发起对话后，这里展示主控调度 / 意图识别 / 路由 / 工具调用（含 Planner 规划与步骤）</p>}
              </div>
            ) : (
              <div className="side-scroll">
                <KnowledgePanel projectId={projectId} />
              </div>
            )}
          </aside>
        </main>
      ) : (
        <main className="trace-main"><TracePanel /></main>
      )}
    </div>
  )
}
