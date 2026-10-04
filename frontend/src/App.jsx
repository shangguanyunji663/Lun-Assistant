import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { api } from './api.js'
import { DEMO_INTERRUPT, DEMO_PROJECTS, DEMO_SESSIONS, DEMO_USER, isDemo } from './demo.js'
import { initPointerFx, stampAt } from './fx.js'
import { AmbientLines, Markdown, Seal } from './components/decor.jsx'
import AuthPage from './components/AuthPage.jsx'
import Timeline from './components/Timeline.jsx'
import TracePanel from './components/TracePanel.jsx'
import KnowledgePanel from './components/KnowledgePanel.jsx'
import ProjectArchive from './components/ProjectArchive.jsx'
import ProjectDialog from './components/ProjectDialog.jsx'
import SkinPicker from './components/SkinPicker.jsx'
import { useChat } from './hooks/useChat.js'
import { useProjects } from './hooks/useProjects.js'
import { useSessions } from './hooks/useSessions.js'
import { useSkin } from './hooks/useSkin.js'
import { useStickyScroll } from './hooks/useStickyScroll.js'

/* ============================================================
   主应用 · v18「六套设计语言」
     · 皮肤：<html data-skin="a…f">，6 套完整设计语言（配色/字体/排版/材质/动效性格）
       整套切换，见 src/skins/*.css 与 skins/registry.js。
     · 结构：三栏（会话卷册 / 对话主区 / 右栏三 tab）；可观测为独立视图。
     · 逻辑层沿用 v12 起的自定义 hooks（对话 SSE / 会话 / 项目），本版未改其内核。
     · 可玩性：会话卷册可拖拽重排；采纳产出时在落点砸一枚图章。
   ============================================================ */

/* ---------------------------------------------------------- 会话卷册
   拖拽重排：按住一行拖动，跨过相邻行时实时交换；松手落定。
   仅用 Pointer 事件，触屏同样可用（touch-action: none 防误滚）。 */
function VolumeList({ sessions, activeId, disabled, onSelect, onRemove, onReorder, fmtTime }) {
  const listRef = useRef(null)
  const [drag, setDrag] = useState(null) // { id, from, delta, axis }

  const begin = (e, s, idx) => {
    if (disabled) return
    const list = listRef.current
    const rects = [...list.querySelectorAll('.wb-vol')].map(el => el.getBoundingClientRect())

    /* 轴向自适应：A/B/C/E/F 的会话栏是左侧竖列（沿 Y 拖），
       而 D「木牍竖排」把它放进了顶部横向书签栏（必须沿 X 拖）——
       竖向位移在横排容器里会被 overflow 裁掉，手感尽失。
       这里按前两项的实际排布判断，不依赖皮肤类名或媒体查询。 */
    const horizontal = rects.length > 1
      && Math.abs(rects[1].left - rects[0].left) > Math.abs(rects[1].top - rects[0].top)
    const axis = horizontal ? 'x' : 'y'
    const step = rects.length > 1
      ? (horizontal ? rects[1].left - rects[0].left : rects[1].top - rects[0].top)
      : (horizontal ? 180 : 74)
    const startAt = horizontal ? e.clientX : e.clientY

    let armed = false
    let delta = 0

    const move = (ev) => {
      delta = (horizontal ? ev.clientX : ev.clientY) - startAt
      if (!armed) {
        if (Math.abs(delta) < 6) return
        armed = true
        setDrag({ id: s.id, from: idx, delta: 0, axis })
      }
      setDrag({ id: s.id, from: idx, delta, axis })
      /* 横排书签栏总宽超过容器：指针贴边时顺带滚动，否则拖不到远处的位次 */
      if (horizontal) {
        const r = list.getBoundingClientRect()
        if (ev.clientX - r.left < 48) list.scrollLeft -= 7
        else if (r.right - ev.clientX < 48) list.scrollLeft += 7
      }
    }

    const up = () => {
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', up)
      if (!armed) { onSelect(s.id); setDrag(null); return }
      // 位移换算成目标位次（相邻项间距固定，取整即可）
      const steps = Math.round(delta / (step || 1))
      const to = Math.max(0, Math.min(sessions.length - 1, idx + steps))
      if (to !== idx) onReorder(idx, to)
      setDrag(null)
    }

    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', up)
  }

  return (
    <div className="wb-vollist" ref={listRef} data-dragging={drag ? 'on' : undefined}>
      {!sessions.length && <p className="wb-vol-empty">尚无会话</p>}
      {sessions.map((s, i) => {
        const d = drag && drag.id === s.id ? drag : null
        const style = d
          ? { transform: d.axis === 'x' ? `translateX(${d.delta}px)` : `translateY(${d.delta}px)` }
          : undefined
        return (
          <div key={s.id}
               className={`wb-vol${s.id === activeId ? ' is-on' : ''}${d ? ' is-dragging' : ''}`}
               /* 拖拽中的项摘掉 data-tilt：否则 fx.css 的
                  [data-tilt].tilt-on 会以 !important 夺走 transform，
                  上面的位移就画不出来了（跟随手感全靠它） */
               data-tilt={disabled || d ? undefined : ''}
               style={style}
               role="button" tabIndex={0}
               aria-pressed={s.id === activeId}
               onPointerDown={e => begin(e, s, i)}
               onKeyDown={e => {
                 if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(s.id) }
               }}
               title={disabled ? '生成中，暂不可切换' : `${s.title}（可拖动排序）`}>
            <span className="wb-vol-no" aria-hidden="true">{String(i + 1).padStart(2, '0')}</span>
            <span className="wb-vol-body">
              <span className="wb-vol-title">{s.title}</span>
              <span className="wb-vol-meta">{fmtTime(s.updatedAt)} · {s.msgs.length} 条</span>
            </span>
            <button className="wb-vol-del" disabled={disabled}
                    onPointerDown={e => e.stopPropagation()}
                    onClick={e => { e.stopPropagation(); onRemove(s.id) }}
                    title="删除会话">×</button>
          </div>
        )
      })}
    </div>
  )
}

/* 开发预览模式（?demo=1）：仅 DEV 构建生效，见 src/demo.js。
   用途是「不起后端也能逐套检查六种设计语言」，生产构建下恒为 false。 */
const DEMO = isDemo()

export default function App() {
  const [user, setUser] = useState(DEMO ? DEMO_USER : null)
  const [booting, setBooting] = useState(!DEMO)
  const [tab, setTab] = useState('chat')
  const [sideTab, setSideTab] = useState('timeline')

  // ---- 皮肤（6 套设计语言）----
  const skinCtl = useSkin()

  // ---- 会话卷册 ----
  const {
    sessions, active, setActiveId, messages, timeline,
    patchSession, newSession: createSession, removeSession: deleteSession, reorderSessions,
  } = useSessions(DEMO ? DEMO_SESSIONS : null)

  /* 粘底滚动：贴底时跟随流式输出；用户上翻历史时暂停跟随，
     并暴露 atBottom 供渲染「回到底部」悬浮按钮。
     依赖用消息/时间线的长度而非数组本身：
     数组身份每轮渲染都变，会让跟随逻辑与滚动位置互相干扰。 */
  const { scrollRef, onScroll, atBottom, scrollToBottom } =
    useStickyScroll([messages.length, timeline.length], active?.id)

  /* ---- 时间线 → 消息 跳转锚 ----
     后端每轮在首次进入 supervisor 时发一次 intent（services/agent/supervisor.py
     的 not visited 分支），node_start 却是每个节点都发——所以 intent 是唯一
     可靠的轮边界。渲染期推断，不动持久化结构：第 k 段事件 → 第 k 条
     assistant 消息（msgs 按 用户/助手 成对追加，助手在奇数下标）。
     首个 intent 之前的事件（error/interrupt 兜底轮）归最后一条消息；
     resume 反馈轮可能不发 intent，其事件会落进上一段——渲染期推断的固有
     边界，收益（老会话全量可跳）大于代价。推断失败返回 -1（不可点）。 */
  const turnOfEvent = useMemo(() => {
    const out = new Array(timeline.length)
    let seg = -1
    for (let i = 0; i < timeline.length; i++) {
      if (timeline[i].type === 'intent') seg += 1
      if (seg < 0) { out[i] = messages.length ? messages.length - 1 : -1; continue }
      const idx = 2 * seg + 1
      out[i] = idx < messages.length ? idx : -1
    }
    return out
  }, [timeline, messages.length])

  /* 点击时间线事件：滚动到对应气泡并脉冲高亮一次。
     流式中目标就是最后一条时直接走粘底的 scrollToBottom，不打断跟随；
     高亮带会话 id，切会话后残留的清理定时器不会错标新会话的气泡。
     注意：scrollRef 是 useStickyScroll 的 callback ref（无 .current），
     查询 DOM 要用这里另挂的 streamElRef——两个 ref 合并挂在同一节点上。 */
  const [jumpHl, setJumpHl] = useState(null) // { sid, idx }
  const hlTimer = useRef(0)
  const streamElRef = useRef(null)
  const attachStream = useCallback((node) => { streamElRef.current = node; scrollRef(node) }, [scrollRef])
  const jumpToMsg = (idx) => {
    if (idx < 0 || idx >= messages.length) return
    if (streaming && idx === messages.length - 1) scrollToBottom('smooth')
    else streamElRef.current
      ?.querySelector(`[data-midx="${idx}"]`)
      ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    setJumpHl({ sid: active?.id, idx })
    window.clearTimeout(hlTimer.current)
    hlTimer.current = window.setTimeout(() => setJumpHl(null), 1300)
  }
  useEffect(() => () => window.clearTimeout(hlTimer.current), [])

  /* 把顶栏实测高度写进 --wb-top-h。
     窄屏（≤820px）下顶栏会换行，各皮肤高度本就不同（实测 165px ~ 234px），
     CSS 里写死任何 vh 数值都会在某个机型上失效——390×844 就曾因此把输入框
     顶出首屏。这里用 ResizeObserver 量出真实高度交给样式层，
     换行、换肤、字号变化都会自动重算。 */
  const topRef = useRef(null)
  useEffect(() => {
    const el = topRef.current
    if (!el) return
    const root = document.documentElement
    const apply = () => root.style.setProperty('--wb-top-h', `${Math.round(el.getBoundingClientRect().height)}px`)
    apply()
    if (typeof ResizeObserver === 'undefined') {
      window.addEventListener('resize', apply)
      return () => window.removeEventListener('resize', apply)
    }
    const ro = new ResizeObserver(apply)
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  // ---- 项目 ----
  const {
    projects, projectsErr, setProjectsErr, projectId, setProjectId,
    archiveKey, setArchiveKey, dialog, setDialog, currentProject,
    createProject, patchProject, deleteProject,
  } = useProjects(user, DEMO ? { projects: DEMO_PROJECTS } : null)

  // ---- 对话发送 / SSE 流式 ----
  const { streaming, interrupt, setInterrupt, input, setInput, send } =
    useChat({ active, patchSession, projectId, setArchiveKey, demo: DEMO })

  /* 演示模式：首屏就把中断确认条摆出来（真实环境由 SSE 的 interrupt 事件触发） */
  const demoSeeded = useRef(false)
  useEffect(() => {
    if (!DEMO || demoSeeded.current) return
    if (!timeline.some(e => e.type === 'interrupt')) return
    demoSeeded.current = true
    setInterrupt(DEMO_INTERRUPT)
  }, [timeline, setInterrupt])

  /* 指针特效（3D 倾斜 / 按钮磁吸 / 点击粒子）：全局挂一次，随应用卸载回收 */
  useEffect(() => initPointerFx(), [])

  /* ---- 自动登录 ---- */
  useEffect(() => {
    if (DEMO) return
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
    setInput('')
  }

  const removeSession = (id) => {
    if (streaming) return
    deleteSession(id)
  }

  const selectSession = (id) => {
    if (streaming) return
    setActiveId(id)
  }

  const fmtTime = (ts) => {
    const d = new Date(ts)
    const now = new Date()
    const sameDay = d.toDateString() === now.toDateString()
    return sameDay
      ? `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
      : `${d.getMonth() + 1}月${d.getDate()}日`
  }

  /* 等宽时钟：部分皮肤（如夜航仪表）用它做「[14:32:07] 主控」式呼号 */
  const fmtClock = (ts) => {
    if (!ts) return ''
    const d = new Date(ts)
    const p = (n) => String(n).padStart(2, '0')
    return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
  }

  /* 采纳类操作：在点击落点砸一枚图章（可玩性反馈，替代平淡的 toast） */
  const answerInterrupt = (e, op) => {
    if (/采纳|通过|确认/.test(op)) stampAt(e.clientX, e.clientY, '匠')
    send(op, op)
  }

  /* 确认反馈：send 的 resume 分支不会清空 input（它只清普通发送的草稿），
     所以这里显式清一次，否则上一条反馈会留在框里，
     下次误按 Enter 就会把旧反馈再发一遍。 */
  const sendBreak = (text, e) => {
    const t = String(text || '').trim()
    if (!t) return
    if (e && /采纳|通过|确认/.test(t)) stampAt(e.clientX, e.clientY, '匠')
    setInput('')
    send(t, t)
  }

  if (booting) {
    return (
      <div className="wb-boot">
        <Seal size={40} />
        <p>正在铺纸研墨…</p>
      </div>
    )
  }
  if (!user) return <AuthPage onLogin={setUser} skinCtl={skinCtl} />

  return (
    <div className="wb">
      <AmbientLines />

      {/* ============================================================ 顶栏 */}
      <header className="wb-top" ref={topRef}>
        <span className="wb-brand">
          <Seal size={26} />
          <span className="wb-brand-text">
            <b>论匠</b>
            <i>LunJiang · 多智能体论文全流程助手</i>
          </span>
        </span>

        <div className="wb-proj">
          <select className="wb-proj-sel"
                  value={projectId ?? ''}
                  onChange={e => setProjectId(e.target.value ? Number(e.target.value) : null)}
                  title="关联的论文项目">
            <option value="">（未关联项目）</option>
            {projects.map(p => <option key={p.id} value={p.id}>{`#${p.id} ${p.title}`}</option>)}
          </select>
          <button className="wb-btn wb-btn-ghost" data-magnet
                  disabled={!projectId}
                  onClick={() => setDialog({ mode: 'edit', project: currentProject })}
                  title={projectId ? '编辑 / 删除当前项目' : '请先选择项目'}>项目设置</button>
          <button className="wb-btn wb-btn-ghost" data-magnet
                  onClick={() => setDialog({ mode: 'create' })}>新建项目</button>
        </div>

        <span className="wb-fill" />

        <SkinPicker {...skinCtl} />

        <nav className="wb-views" aria-label="视图">
          <button className={`wb-view${tab === 'chat' ? ' is-on' : ''}`}
                  onClick={() => setTab('chat')}>对话</button>
          <button className={`wb-view${tab === 'trace' ? ' is-on' : ''}`}
                  onClick={() => setTab('trace')}
                  title={user.role !== 'admin' ? '仅 admin 可见 Trace 数据' : ''}>可观测</button>
        </nav>

        <span className="wb-user">
          <b>{user.username}</b><i>{user.role}</i>
        </span>
        <button className="wb-btn wb-btn-ghost wb-exit"
                onClick={() => { localStorage.removeItem('lj_token'); setUser(null) }}>退出</button>
      </header>

      {/* ============================================================ 横幅 */}
      {projectsErr && (
        <div className="wb-banner is-err">
          {projectsErr}
          <button className="wb-banner-x" onClick={() => setProjectsErr('')} aria-label="关闭">×</button>
        </div>
      )}
      {user.role !== 'admin' && tab === 'trace' && (
        <div className="wb-banner is-warn">
          当前账号为 {user.role}，Trace 列表需要 admin 权限，此页面将无法加载数据。
        </div>
      )}

      {dialog && (
        <ProjectDialog mode={dialog.mode} initial={dialog.project}
          onClose={() => setDialog(null)}
          onCreate={createProject} onPatch={patchProject} onDelete={deleteProject} />
      )}

      {/* ============================================================ 主体 */}
      {tab === 'chat' ? (
        <main className="wb-body">
          {/* ---------- 左 · 会话卷册 ---------- */}
          <aside className="wb-col wb-volumes">
            <div className="wb-colhead">
              <span className="wb-ch-en">Volumes</span>
              <span className="wb-fill" />
              <span className="wb-ch-cn">会话卷册</span>
            </div>
            <button className="wb-new" data-magnet onClick={newSession} disabled={streaming}>
              <span aria-hidden="true">＋</span> 新建会话
            </button>
            <VolumeList
              sessions={sessions} activeId={active?.id} disabled={streaming}
              onSelect={selectSession} onRemove={removeSession}
              onReorder={reorderSessions} fmtTime={fmtTime} />
          </aside>

          {/* ---------- 中 · 对话主区 ---------- */}
          <section className={`wb-col wb-main${streaming ? ' is-streaming' : ''}`}>
            <div className="wb-stream" ref={attachStream} onScroll={onScroll}>
              <div className="wb-inner">
                {messages.length === 0 && (
                  <div className="wb-empty">
                    <Seal size={44} />
                    <h2>落笔之前</h2>
                    <p className="wb-empty-lead">
                      写下你的论文需求：选题、文献、写作、格式、查重、答辩，
                      各环节都有专项助手接手推进。
                    </p>
                    <div className="wb-prompts">
                      {['帮我确定一个可行的论文选题', '检索近三年大模型相关文献', '为第三章写一段方法论初稿']
                        .map(p => (
                          <button key={p} className="wb-prompt" data-magnet data-burst
                                  onClick={() => send(p)}>{p}</button>
                        ))}
                    </div>
                  </div>
                )}

                {messages.map((m, i) => {
                  const isUser = m.role === 'user'
                  const last = i === messages.length - 1
                  const hl = jumpHl && jumpHl.sid === active?.id && jumpHl.idx === i
                  return (
                    <article key={i} data-midx={i}
                             className={`wb-msg ${isUser ? 'is-user' : 'is-ai'}${hl ? ' is-jump-hl' : ''}`}>
                      <div className="wb-msg-head">
                        <span className="wb-msg-mark" aria-hidden="true">{isUser ? '言' : '匠'}</span>
                        <span className="wb-msg-name">{isUser ? user.username : '匠'}</span>
                        <span className="wb-msg-role">{isUser ? 'USER' : 'MAIN AGENT'}</span>
                        <span className="wb-fill" />
                        <time className="wb-msg-time">{fmtClock(m.ts)}</time>
                      </div>
                      <div className="wb-bubble">
                        {isUser ? m.content : (
                          <>
                            <Markdown>{m.content}</Markdown>
                            {streaming && last && <span className="cursor" aria-hidden="true" />}
                          </>
                        )}
                      </div>
                    </article>
                  )
                })}
              </div>

              {/* 用户上翻历史时给出的回底入口 ——
                  粘底 hook 判定离开底部才出现，不打断正常阅读 */}
              {!atBottom && (
                <button type="button" className="wb-jump" data-magnet
                        onClick={() => scrollToBottom('smooth')}>
                  <span aria-hidden="true">↓</span> 回到底部
                </button>
              )}
            </div>

            {/* 中断确认条 */}
            {interrupt && (
              <div className="wb-break" data-tilt>
                <div className="wb-break-head">
                  <span className="wb-break-badge">待确认</span>
                  <span className="wb-break-note">HUMAN-IN-THE-LOOP</span>
                  <span className="wb-fill" />
                  <span className="wb-break-note">需要你的决定</span>
                </div>
                <p className="wb-break-ask">{interrupt.question || '请确认下一步操作'}</p>
                <div className="wb-break-ops">
                  {(interrupt.options || []).map(op => (
                    <button key={op} className="wb-break-op" data-magnet data-burst
                            onClick={e => answerInterrupt(e, op)}
                            disabled={streaming}>{op}</button>
                  ))}
                  <input className="wb-break-input" placeholder="或输入你的反馈…"
                         value={input}
                         onChange={e => setInput(e.target.value)}
                         onKeyDown={e => {
                           if (e.key === 'Enter' && input.trim()) {
                             e.preventDefault()
                             sendBreak(input.trim())
                           }
                         }} />
                  <button className="wb-btn wb-btn-ink"
                          onClick={e => sendBreak(input.trim(), e)}
                          disabled={streaming || !input.trim()}>发送反馈</button>
                </div>
              </div>
            )}

            {/* 输入区 */}
            <div className="wb-compose">
              <div className="wb-compose-box">
                <textarea className="wb-compose-ta" rows={2}
                          placeholder="输入论文相关请求，如：帮我找几篇大模型文献 / 帮我写摘要…"
                          value={input}
                          disabled={streaming || !!interrupt}
                          onChange={e => setInput(e.target.value)}
                          onKeyDown={e => {
                            if (e.key === 'Enter' && !e.shiftKey && input.trim()) {
                              e.preventDefault()
                              send(input.trim())
                            }
                          }} />
                <button className={`wb-compose-send wb-btn wb-btn-ink${streaming ? ' is-busy' : ''}`}
                        data-magnet
                        disabled={streaming || !input.trim() || !!interrupt}
                        onClick={() => send(input.trim())}>
                  {streaming ? '生成中…' : '发送'}
                </button>
              </div>
              <p className="wb-compose-hint">
                Enter 发送 · Shift + Enter 换行
                {projectId ? ` · 已关联项目 #${projectId}` : ' · 未关联项目（对话不使用项目知识库）'}
              </p>
            </div>
          </section>

          {/* ---------- 右 · 可观测 / 知识库 / 档案 ---------- */}
          <aside className="wb-col wb-side">
            <nav className="wb-side-tabs" aria-label="侧栏">
              <button className={`wb-side-tab${sideTab === 'timeline' ? ' is-on' : ''}`}
                      onClick={() => setSideTab('timeline')}>执行时间线</button>
              <button className={`wb-side-tab${sideTab === 'knowledge' ? ' is-on' : ''}`}
                      onClick={() => setSideTab('knowledge')}>项目知识库</button>
              <button className={`wb-side-tab${sideTab === 'archive' ? ' is-on' : ''}`}
                      onClick={() => setSideTab('archive')}>项目档案</button>
            </nav>
            <div className="wb-side-body">
              {sideTab === 'timeline' && (
                timeline.length
                  ? <Timeline events={timeline} turnOf={turnOfEvent}
                              onJump={i => jumpToMsg(turnOfEvent[i] ?? -1)} />
                  : <p className="empty-tip">
                      发起对话后，这里展示主控调度 / 意图识别 / 路由 / 工具调用
                      （含 Planner 规划与步骤）。
                    </p>
              )}
              {sideTab === 'knowledge' && <KnowledgePanel projectId={projectId} demo={DEMO} />}
              {sideTab === 'archive' && (
                <ProjectArchive projectId={projectId} refreshKey={archiveKey} demo={DEMO}
                                onEdit={() => setDialog({ mode: 'edit', project: currentProject })} />
              )}
            </div>
          </aside>
        </main>
      ) : (
        <main className="wb-trace-main"><TracePanel demo={DEMO} /></main>
      )}
    </div>
  )
}