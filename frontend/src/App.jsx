import React, { useEffect, useRef, useState } from 'react'
import { api, sse } from './api.js'
import InkBackground from './InkBackground.jsx'
import { Seal, Markdown, WoodRoll } from './components/decor.jsx'
import AuthPage from './components/AuthPage.jsx'
import Timeline from './components/Timeline.jsx'
import TracePanel from './components/TracePanel.jsx'
import KnowledgePanel from './components/KnowledgePanel.jsx'
import ProjectArchive from './components/ProjectArchive.jsx'
import ProjectDialog from './components/ProjectDialog.jsx'

/* ============================================================
   主应用：卷轴木轴 + 会话卷册 + 对话主区 + 右栏三 tab
   ============================================================ */

const LS_KEY = 'lj_sessions_v1'
const MAX_SESSIONS = 30

const makeId = () => `web-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`

/** 会话标题：取首条用户消息前 18 字 */
const titleOf = (text) => {
  const t = String(text || '').replace(/\s+/g, ' ').trim()
  return t ? (t.length > 18 ? t.slice(0, 18) + '…' : t) : '新会话'
}

const loadSessions = () => {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (!raw) return []
    const list = JSON.parse(raw)
    return Array.isArray(list) ? list.filter(s => s && s.id) : []
  } catch { return [] }
}

export default function App() {
  const [user, setUser] = useState(null)
  const [booting, setBooting] = useState(true)
  const [tab, setTab] = useState('chat')
  const [projects, setProjects] = useState([])
  const [projectsErr, setProjectsErr] = useState('')
  const [projectId, setProjectId] = useState(null)
  const [archiveKey, setArchiveKey] = useState(0)
  const [dialog, setDialog] = useState(null)          // {mode:'create'|'edit', project?}

  // 会话卷册（原单会话全局 state 改为多会话）
  const [sessions, setSessions] = useState(loadSessions)
  const [activeId, setActiveId] = useState(null)
  const [streaming, setStreaming] = useState(false)
  const [interrupt, setInterrupt] = useState(null)
  const [input, setInput] = useState('')
  const [sideTab, setSideTab] = useState('timeline')
  const bottomRef = useRef(null)

  /* 山水浓度：AI 底图不透明度，用户可实时调节并持久化 */
  const [inkOp, setInkOp] = useState(() => {
    const v = Number(localStorage.getItem('lj_ink_op'))
    return Number.isFinite(v) && v >= 0 && v <= 0.4 ? v : 0.16
  })
  useEffect(() => {
    document.documentElement.style.setProperty('--ink-photo-op', String(inkOp))
    try { localStorage.setItem('lj_ink_op', String(inkOp)) } catch { /* 隐私模式忽略 */ }
  }, [inkOp])

  /* 调参台联动：监听 storage 事件（跨 tab）。
     用户在 console/tuner.html 改 lj_theme / lj_ink_op 后，主应用实时生效。
     白名单与下方 [theme, setTheme] 一致：当前 a/b/c/d 共 4 主题。 */
  useEffect(() => {
    const onStorage = (e) => {
      if (e.key === 'lj_theme' && ['a','b','c','d'].includes(e.newValue)) {
        setTheme(e.newValue)
      } else if (e.key === 'lj_ink_op') {
        const v = Number(e.newValue)
        if (Number.isFinite(v) && v >= 0 && v <= 0.4) setInkOp(v)
      }
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  /* v11 · 四主题切换（A 柔雾青绿 / B 水墨留白 / C 暗墨夜山 / D 青绿金碧）。
     持久化到 localStorage.lj_theme；初始化时若 localStorage 没值则读 :root 默认的 data-theme，
     否则从 localStorage 取。新增 D 主题对应青绿金碧参考图（Traditional Chinese blue-green）。 */
  const [theme, setTheme] = useState(() => {
    const t = localStorage.getItem('lj_theme')
    return ['a','b','c','d'].includes(t) ? t : 'a'
  })
  useEffect(() => {
    document.body.dataset.theme = theme
    try { localStorage.setItem('lj_theme', theme) } catch { /* 隐私模式忽略 */ }
    // 主题切换音效：Web Audio API 程序化生成短"卷轴松开"咔哒声；零外部资产
    // 仅在用户已与页面交互后（autoplay 策略），故 try/catch 包裹隐私模式 / iOS 静音
    if (themeTickRef.current) {
      try {
        const AC = window.AudioContext || window.webkitAudioContext
        if (AC) {
          const ac = new AC()
          const osc = ac.createOscillator(), gain = ac.createGain()
          osc.type = 'triangle'
          osc.frequency.setValueAtTime(880, ac.currentTime)
          osc.frequency.exponentialRampToValueAtTime(220, ac.currentTime + 0.15)
          gain.gain.setValueAtTime(0.06, ac.currentTime)
          gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 0.18)
          osc.connect(gain).connect(ac.destination)
          osc.start(ac.currentTime); osc.stop(ac.currentTime + 0.20)
          setTimeout(() => ac.close(), 250)
        }
      } catch { /* autoplay blocked or audio disabled */ }
    }
    themeTickRef.current = true
  }, [theme])

  /* ref: 首次 mount 时不响（避免 reload 主题后立刻播放） */
  const themeTickRef = useRef(false)

  /* chip 取各主题底色（A 略深一档以免在浅底上糊掉），B/C/D 与 styles.css 的 --bg-deep 一致 */
  const THEMES = [
    { id: 'a', label: '柔雾青绿', chip: '#C5DBE8' },
    { id: 'b', label: '黑白瑞士', chip: '#000000' },
    { id: 'c', label: '暗墨夜山', chip: '#0A1424' },
    { id: 'd', label: '青绿金碧', chip: '#C9B58A' },
  ]

  const active = sessions.find(s => s.id === activeId) || sessions[0] || null
  const messages = active?.msgs ?? []
  const timeline = active?.timeline ?? []

  /* ---- 自动登录 ---- */
  useEffect(() => {
    const t = localStorage.getItem('lj_token')
    if (!t) { setBooting(false); return }
    api.me().then(u => setUser(u)).catch(e => {
      console.warn('[me] 自动登录失败:', e)
      localStorage.removeItem('lj_token')
    }).finally(() => setBooting(false))
  }, [])

  /* ---- 项目列表 ---- */
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

  /* ---- 确保至少有一个会话 ---- */
  useEffect(() => {
    if (!sessions.length) {
      const s = { id: makeId(), title: '新会话', msgs: [], timeline: [], updatedAt: Date.now() }
      setSessions([s]); setActiveId(s.id)
    } else if (!sessions.some(s => s.id === activeId)) {
      setActiveId(sessions[0].id)
    }
  }, [sessions, activeId])

  /* ---- 持久化 ---- */
  useEffect(() => {
    try { localStorage.setItem(LS_KEY, JSON.stringify(sessions.slice(0, MAX_SESSIONS))) } catch {}
  }, [sessions])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, timeline])

  if (booting) return <div className="center muted">加载中…</div>
  if (!user) return <AuthPage onLogin={setUser} />

  const patchSession = (id, fn) =>
    setSessions(list => list.map(s => (s.id === id ? { ...fn(s), updatedAt: Date.now() } : s)))

  const newSession = () => {
    if (streaming) return
    const s = { id: makeId(), title: '新会话', msgs: [], timeline: [], updatedAt: Date.now() }
    setSessions(list => [s, ...list].slice(0, MAX_SESSIONS))
    setActiveId(s.id)
    setInterrupt(null)
    setInput('')
  }

  const removeSession = (id) => {
    if (streaming) return
    setSessions(list => {
      const rest = list.filter(s => s.id !== id)
      if (rest.length) { if (id === activeId) setActiveId(rest[0].id); return rest }
      const s = { id: makeId(), title: '新会话', msgs: [], timeline: [], updatedAt: Date.now() }
      setActiveId(s.id)
      return [s]
    })
  }

  const send = async (text, resume = null) => {
    if (streaming || !active) return
    const sid = active.id
    const body = resume ? `[确认反馈] ${resume}` : text

    setStreaming(true)
    setInterrupt(null)
    if (!resume) setInput('')

    // 追加用户消息；若为本会话首条，用它作标题
    patchSession(sid, s => ({
      ...s,
      title: s.msgs.length ? s.title : titleOf(text),
      msgs: [...s.msgs, { role: 'user', content: body }],
    }))
    // 占位助手消息
    patchSession(sid, s => ({ ...s, msgs: [...s.msgs, { role: 'assistant', content: '' }] }))

    let acc = ''
    const patchLast = (content) =>
      patchSession(sid, s => {
        if (!s.msgs.length) return s
        const c = [...s.msgs]
        c[c.length - 1] = { role: 'assistant', content }
        return { ...s, msgs: c }
      })

    try {
      const finalText = await sse(resume ? '/agent/resume' : '/agent/chat',
        resume
          ? { session_id: sid, feedback: resume, project_id: projectId }
          : { session_id: sid, message: text, project_id: projectId },
        (type, payload, node) => {
          if (type === 'token') { acc += payload || ''; patchLast(acc) }
          else if (type === 'final') { if (payload?.output) patchLast(payload.output) }
          else if (type === 'interrupt') {
            setInterrupt(payload)
            patchSession(sid, s => ({ ...s, timeline: [...s.timeline, { type: 'interrupt', payload, node }] }))
          } else if (type === 'error') {
            patchSession(sid, s => ({ ...s, timeline: [...s.timeline, { type: 'error', payload, node }] }))
          } else if (['node_start', 'node_end', 'intent', 'route', 'plan', 'step_event'].includes(type)) {
            patchSession(sid, s => ({ ...s, timeline: [...s.timeline, { type, payload, node }] }))
          }
        })
      if (finalText) patchLast(finalText)
      if (projectId) setArchiveKey(k => k + 1)
    } catch (e) {
      patchLast(`请求失败：${e.message || e}`)
      console.warn('[chat]', e)
    } finally { setStreaming(false) }
  }

  /* ---- 项目 CRUD ---- */
  const createProject = async (title, major, requirement) => {
    const p = await api.createProject(title, major, requirement)
    setProjects(ps => [p, ...ps]); setProjectId(p.id); setProjectsErr('')
  }
  const patchProject = async (patch) => {
    await api.patchProject(projectId, patch)
    setProjects(ps => ps.map(p => p.id === projectId ? { ...p, ...patch } : p))
    setArchiveKey(k => k + 1)
  }
  const deleteProject = async () => {
    await api.deleteProject(projectId)
    setProjects(ps => ps.filter(p => p.id !== projectId))
    setProjectId(null); setDialog(null)
  }

  const currentProject = projects.find(p => p.id === projectId) || null
  const fmtTime = (ts) => {
    const d = new Date(ts), now = new Date()
    const sameDay = d.toDateString() === now.toDateString()
    return sameDay
      ? `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
      : `${d.getMonth() + 1}月${d.getDate()}日`
  }

  return (
    <div className="app">
      <InkBackground />
      <WoodRoll />

      <header className="topbar">
        <h1 className="brand"><Seal size={26} />论匠<small>多智能体论文全流程助手</small></h1>
        <div className="spacer" />

        <div className="proj-picker">
          <select value={projectId ?? ''} onChange={e => setProjectId(e.target.value ? Number(e.target.value) : null)}>
            <option value="">（未关联项目）</option>
            {projects.map(p => <option key={p.id} value={p.id}>{`#${p.id} ${p.title}`}</option>)}
          </select>
          <button className="btn btn-ghost btn-sm" disabled={!projectId}
                  onClick={() => setDialog({ mode: 'edit', project: currentProject })}
                  title={projectId ? '编辑 / 删除当前项目' : '请先选择项目'}>项目设置</button>
          <button className="btn btn-ghost btn-sm" onClick={() => setDialog({ mode: 'create' })}>＋ 新建</button>
        </div>

        {/* 山水浓度：实时调 AI 底图不透明度 */}
        <div className="ink-tuner" title="调节山水底图浓度。0 = 纯色底；超过 0.30 山形开始与文字争注意力">
          <span className="lab">山水</span>
          <input type="range" min="0" max="0.4" step="0.01" value={inkOp}
                 onChange={e => setInkOp(Number(e.target.value))}
                 aria-label="山水底图浓度" />
          <span className="val">{inkOp.toFixed(2)}</span>
        </div>

        {/* 调参台入口：跳转生产版控制台（frontend/public/console/tuner.html）。
            调参台改的主题 / 山水浓度会经 localStorage + storage 事件实时同步回主应用。 */}
        <a className="btn btn-ghost btn-sm console-entry" href="console/tuner.html" target="_blank" rel="noreferrer"
           title="打开透明度调参台（多维度调节 + WCAG 实时测算，改动实时同步回本页）">🎛 控制台</a>

        {/* v11 · 四主题切换（A 柔雾青绿 / B 水墨留白 / C 暗墨夜山 / D 青绿金碧）。
            单击切换整套配色 + 背景图 + 卷轴语言；持久化到 localStorage.lj_theme。 */}
        <div className="theme-tabs" role="tablist" aria-label="主题切换">
          {THEMES.map(t => (
            <button key={t.id}
                    role="tab"
                    aria-selected={theme === t.id}
                    className={theme === t.id ? 'on' : ''}
                    title={`${t.label}${theme === t.id ? '（当前）' : ''}`}
                    onClick={() => setTheme(t.id)}>
              <span className="chip" style={{background: t.chip}} />
              {t.label}
            </button>
          ))}
        </div>

        <nav>
          <button className={tab === 'chat' ? 'on' : ''} onClick={() => setTab('chat')}>对话</button>
          <button className={tab === 'trace' ? 'on' : ''} onClick={() => setTab('trace')}
                  title={user.role !== 'admin' ? '仅 admin 可见 Trace 数据' : ''}>可观测</button>
        </nav>

        <span className="who">{user.username}<em>{user.role}</em></span>
        <button className="btn btn-ghost" onClick={() => { localStorage.removeItem('lj_token'); setUser(null) }}>退出</button>
      </header>

      {projectsErr && <div className="top-banner err">{projectsErr} <span className="link" onClick={() => setProjectsErr('')}>×</span></div>}
      {user.role !== 'admin' && tab === 'trace' && (
        <div className="top-banner warn">当前账号为 {user.role}，Trace 列表需要 admin 权限，此页面将无法加载数据。</div>
      )}

      {dialog && (
        <ProjectDialog mode={dialog.mode} initial={dialog.project}
          onClose={() => setDialog(null)}
          onCreate={createProject} onPatch={patchProject} onDelete={deleteProject} />
      )}

      {tab === 'chat' ? (
        <main className="chat-layout">
          {/* 会话卷册 */}
          <aside className="sessions">
            <div className="sess-head">
              <span className="t">会话卷册</span>
              <button className="btn btn-ghost btn-sm" onClick={newSession}
                      disabled={streaming} title="新建会话">＋</button>
            </div>
            <div className="sess-list">
              {sessions.length === 0 && <div className="sess-empty">尚无会话</div>}
              {sessions.map(s => (
                <div key={s.id}
                     className={`sess-item${s.id === active?.id ? ' on' : ''}`}
                     onClick={() => { if (!streaming) { setActiveId(s.id); setInterrupt(null) } }}
                     title={streaming ? '生成中，暂不可切换' : s.title}>
                  <div className="sess-title">{s.title}</div>
                  <div className="sess-meta">{fmtTime(s.updatedAt)} · {s.msgs.length} 条</div>
                  <button className="sess-del" disabled={streaming}
                          onClick={e => { e.stopPropagation(); removeSession(s.id) }}
                          title="删除会话">×</button>
                </div>
              ))}
            </div>
          </aside>

          <section className="chat-col">
            <div className="messages">
              <div className="msgs-inner">
                {messages.length === 0 && (
                  <div className="empty-state">
                    <Seal size={44} />
                    <h2>落笔之前</h2>
                    <p>描述你的论文需求，主控 Agent 会调度选题、文献、写作、格式、查重与答辩六类专项 Agent 协同完成。</p>
                    <div className="prompts">
                      {['帮我确定一个可行的论文选题', '检索近三年大模型相关文献', '为第三章写一段方法论初稿']
                        .map(p => <button key={p} className="btn btn-ghost btn-sm" onClick={() => send(p)}>{p}</button>)}
                    </div>
                  </div>
                )}
                {messages.map((m, i) => (
                  <div key={i} className={`msg ${m.role}`}>
                    <div className="msg-mark">{m.role === 'user' ? '言' : '匠'}</div>
                    <div className="bubble">
                      {m.role === 'assistant'
                        ? <Markdown>{m.content || (streaming && i === messages.length - 1 ? '…' : '')}</Markdown>
                        : m.content}
                    </div>
                  </div>
                ))}
                <div ref={bottomRef} />
              </div>
            </div>

            {interrupt && (
              <div className="interrupt-bar">
                <span className="ib-q">⏸ {interrupt.question || 'Agent 需要你的确认'}</span>
                <div className="ib-opts">
                  {(interrupt.options || []).map(op => (
                    <button key={op} className="btn btn-ghost btn-sm" onClick={() => send(op, op)} disabled={streaming}>{op}</button>
                  ))}
                </div>
                <div className="free-form">
                  <input placeholder="输入你的反馈…" value={input}
                         onChange={e => setInput(e.target.value)}
                         onKeyDown={e => e.key === 'Enter' && input && send(input, input)} />
                  <button className="btn btn-ink btn-sm" onClick={() => input && send(input, input)} disabled={streaming || !input}>发送反馈</button>
                </div>
              </div>
            )}

            <div className="input-bar">
              <div className="composer">
                <textarea rows={2} placeholder="输入论文相关请求，如：帮我找几篇大模型文献 / 帮我写摘要…" value={input}
                          disabled={streaming || !!interrupt}
                          onChange={e => setInput(e.target.value)}
                          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && input.trim()) { e.preventDefault(); send(input.trim()) } }} />
                <button className="btn btn-ink send" disabled={streaming || !input.trim() || !!interrupt}
                        onClick={() => send(input.trim())}>
                  {streaming ? '生成中…' : '发送'}
                </button>
              </div>
              <div className="input-hint">Enter 发送 · Shift + Enter 换行{projectId ? ` · 已关联项目 #${projectId}` : ' · 未关联项目（对话不使用项目知识库）'}</div>
            </div>
          </section>

          <aside className="side-col">
            <div className="side-tabs">
              <button className={sideTab === 'timeline' ? 'on' : ''} onClick={() => setSideTab('timeline')}>执行时间线</button>
              <button className={sideTab === 'knowledge' ? 'on' : ''} onClick={() => setSideTab('knowledge')}>项目知识库</button>
              <button className={sideTab === 'archive' ? 'on' : ''} onClick={() => setSideTab('archive')}>项目档案</button>
            </div>
            <div className="side-scroll">
              {sideTab === 'timeline' ? (
                <>
                  <Timeline events={timeline} />
                  {!timeline.length &&
                    <p className="muted empty-tip">发起对话后，这里展示主控调度 / 意图识别 / 路由 / 工具调用（含 Planner 规划与步骤）。</p>}
                </>
              ) : sideTab === 'knowledge' ? (
                <KnowledgePanel projectId={projectId} />
              ) : (
                <ProjectArchive projectId={projectId} refreshKey={archiveKey}
                                onEdit={() => setDialog({ mode: 'edit', project: currentProject })} />
              )}
            </div>
          </aside>
        </main>
      ) : (
        <main className="trace-main"><TracePanel /></main>
      )}
    </div>
  )
}
