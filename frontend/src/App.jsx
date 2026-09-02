import React, { useEffect, useState } from 'react'
import { api } from './api.js'
import InkBackground from './InkBackground.jsx'
import { Seal, Markdown, WoodRoll } from './components/decor.jsx'
import AuthPage from './components/AuthPage.jsx'
import Timeline from './components/Timeline.jsx'
import TracePanel from './components/TracePanel.jsx'
import KnowledgePanel from './components/KnowledgePanel.jsx'
import ProjectArchive from './components/ProjectArchive.jsx'
import ProjectDialog from './components/ProjectDialog.jsx'
import { useChat } from './hooks/useChat.js'
import { useProjects } from './hooks/useProjects.js'
import { useSessions } from './hooks/useSessions.js'
import { useTheme } from './hooks/useTheme.js'

/* ============================================================
   主应用：卷轴木轴 + 会话卷册 + 对话主区 + 右栏三 tab
   状态逻辑已拆分至 src/hooks/（主题 / 会话 / 项目 / 对话）
   ============================================================ */

export default function App() {
  const [user, setUser] = useState(null)
  const [booting, setBooting] = useState(true)
  const [tab, setTab] = useState('chat')
  const [sideTab, setSideTab] = useState('timeline')

  // ---- 主题 + 山水浓度 ----
  const { theme, setTheme, inkOp, setInkOp, THEMES } = useTheme()

  // ---- 会话卷册 ----
  const {
    sessions, active, setActiveId, messages, timeline, bottomRef,
    patchSession, newSession: createSession, removeSession: deleteSession,
  } = useSessions()

  // ---- 项目 ----
  const {
    projects, projectsErr, setProjectsErr, projectId, setProjectId,
    archiveKey, setArchiveKey, dialog, setDialog, currentProject,
    createProject, patchProject, deleteProject,
  } = useProjects(user)

  // ---- 对话发送 / SSE 流式 ----
  const { streaming, interrupt, setInterrupt, input, setInput, send } =
    useChat({ active, patchSession, projectId, setArchiveKey })

  /* ---- 自动登录 ---- */
  useEffect(() => {
    const t = localStorage.getItem('lj_token')
    if (!t) { setBooting(false); return }
    api.me().then(u => setUser(u)).catch(e => {
      console.warn('[me] 自动登录失败:', e)
      localStorage.removeItem('lj_token')
    }).finally(() => setBooting(false))
  }, [])

  /* ---- 会话增删（生成中锁定）---- */
  const newSession = () => {
    if (streaming) return
    createSession()
    setInterrupt(null)
    setInput('')
  }

  const removeSession = (id) => {
    if (streaming) return
    deleteSession(id)
  }

  const selectSession = (id) => {
    if (streaming) return
    setActiveId(id)
    setInterrupt(null)
  }

  const fmtTime = (ts) => {
    const d = new Date(ts)
    const now = new Date()
    const sameDay = d.toDateString() === now.toDateString()
    return sameDay
      ? `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
      : `${d.getMonth() + 1}月${d.getDate()}日`
  }

  // bottomRef 为自定义 hook 返回的稳定 ref，静态分析无法识别其身份，无需加入依赖
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, timeline])

  if (booting) return <div className="center muted">加载中…</div>
  if (!user) return <AuthPage onLogin={setUser} />

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
              <span className="chip" style={{ background: t.chip }} />
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
                     onClick={() => selectSession(s.id)}
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
