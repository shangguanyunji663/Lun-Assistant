import { useEffect, useRef, useState } from 'react'

const LS_KEY = 'lj_sessions_v1'
const MAX_SESSIONS = 30
/* 持久化节流（ms）：打字机每 24ms 改一次 sessions，
   原实现每次都 JSON.stringify 全量会话写盘 —— 多轮长对话下
   单条消息即可达数 MB，既卡顿又很快撞上 localStorage 5MB 配额。 */
const PERSIST_DEBOUNCE_MS = 500

const makeId = () => `web-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`

/** 会话标题：取首条用户消息前 18 字 */
export const titleOf = (text) => {
  const t = String(text || '').replace(/\s+/g, ' ').trim()
  return t ? (t.length > 18 ? t.slice(0, 18) + '…' : t) : '新会话'
}

/* interrupt：该会话待确认的人机介入项（由 useChat 写入）。
   显式建字段而非靠 `s.interrupt ?? null` 兜底，是为了让
   JSON.stringify 的形状稳定，便于持久化比对与调试。 */
const emptySession = () => ({
  id: makeId(), title: '新会话', msgs: [], timeline: [],
  interrupt: null, updatedAt: Date.now(),
})

/* 归一化单条会话：localStorage 里的数据可能来自旧版本或被手工改坏，
   缺 msgs/timeline 会让渲染期 s.msgs.map 直接抛错白屏。 */
const normalize = (s) => ({
  id: String(s.id),
  title: typeof s.title === 'string' ? s.title : '新会话',
  msgs: Array.isArray(s.msgs) ? s.msgs.filter(m => m && typeof m.content === 'string') : [],
  timeline: Array.isArray(s.timeline) ? s.timeline.filter(e => e && typeof e.type === 'string') : [],
  interrupt: s.interrupt && typeof s.interrupt === 'object' ? s.interrupt : null,
  updatedAt: Number(s.updatedAt) || Date.now(),
})

const loadSessions = () => {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (!raw) return []
    const list = JSON.parse(raw)
    if (!Array.isArray(list)) return []
    return list.filter(s => s && s.id).map(normalize)
  } catch {
    // 数据损坏：宁可从空会话开始，也不要让整个应用崩在启动态
    try { localStorage.removeItem(LS_KEY) } catch { /* 隐私模式忽略 */ }
    return []
  }
}

/**
 * 多会话卷册管理：
 * - 会话列表 / 当前会话，localStorage 持久化（上限 MAX_SESSIONS）；
 * - 保证至少存在一个会话；patchSession 供 SSE 增量更新会话内容；
 * - reorderSessions 供拖拽重排（v18 可玩性）；
 * - seed：显式传入的初始会话（开发预览模式用）；给了 seed 就忽略本地持久化，
 *   保证演示数据每次都一致，不被上一次残留的 localStorage 覆盖。
 */
export function useSessions(seed = null) {
  const [sessions, setSessions] = useState(() => (seed ? seed.map(normalize) : loadSessions()))
  const [activeId, setActiveId] = useState(null)
  const persistTimer = useRef(0)

  /* 确保至少有一个会话 */
  useEffect(() => {
    if (!sessions.length) {
      const s = emptySession()
      setSessions([s]); setActiveId(s.id)
    } else if (!sessions.some(s => s.id === activeId)) {
      setActiveId(sessions[0].id)
    }
  }, [sessions, activeId])

  /* 持久化：节流写盘。
     另：updatedAt 在每次 patch 时被刷新（见 patchSession），
     流式期间等于每 24ms 写一次全量 JSON —— 必须合并。 */
  useEffect(() => {
    /* 演示模式（?demo=1）绝不写盘：seed 是 mock 数据，
       写进去会把用户真实的会话卷册整个覆盖掉，且不可恢复。 */
    if (seed) return
    if (persistTimer.current) window.clearTimeout(persistTimer.current)
    persistTimer.current = window.setTimeout(() => {
      persistTimer.current = 0
      try {
        localStorage.setItem(LS_KEY, JSON.stringify(sessions.slice(0, MAX_SESSIONS)))
      } catch (e) {
        // 配额超限：丢弃最旧的会话后重试一次，仍失败则放弃本次持久化，
        // 但绝不能让写盘异常冒泡把对话界面打断。
        console.warn('[sessions] 本地持久化失败:', e)
        try {
          localStorage.setItem(LS_KEY, JSON.stringify(sessions.slice(0, 5)))
        } catch { /* 隐私模式或仍超限：放弃 */ }
      }
    }, PERSIST_DEBOUNCE_MS)
    return () => { if (persistTimer.current) window.clearTimeout(persistTimer.current) }
  }, [sessions, seed])

  /* patchSession(sid, fn)：按 id 定位并合并。
     updatedAt 只在「消息条数变化」时刷新——流式期间逐 token 刷新会让
     卷册排序与持久化频率一起飙升，而秒级精度对「最近更新」无意义。 */
  const patchSession = (id, fn) =>
    setSessions(list => list.map(s => {
      if (s.id !== id) return s
      const next = fn(s)
      const grew = next.msgs.length !== s.msgs.length
      return { ...next, updatedAt: grew ? Date.now() : s.updatedAt }
    }))

  const newSession = () => {
    const s = emptySession()
    setSessions(list => [s, ...list].slice(0, MAX_SESSIONS))
    setActiveId(s.id)
  }

  /* 删除会话。
     原实现在 setSessions 的 updater 内部调用 setActiveId —— updater 必须是
     纯函数，StrictMode 下会被双调用并产生重复 setState。
     现在只更新列表：activeId 由上面的「确保至少一个会话 / activeId 有效」
     effect 统一兜底（它已在做同样的校正），职责单一且无副作用。 */
  const removeSession = (id) => {
    setSessions(list => {
      const rest = list.filter(s => s.id !== id)
      return rest.length ? rest : [emptySession()]
    })
  }

  /** 拖拽重排（v18 可玩性）：把 from 位置的会话移到 to 位置 */
  const reorderSessions = (from, to) => {
    setSessions(list => {
      if (from === to || from < 0 || to < 0 || from >= list.length || to >= list.length) return list
      const next = [...list]
      const [moved] = next.splice(from, 1)
      next.splice(to, 0, moved)
      return next
    })
  }

  const active = sessions.find(s => s.id === activeId) || sessions[0] || null
  const messages = active?.msgs ?? []
  const timeline = active?.timeline ?? []

  return {
    sessions, active, activeId, setActiveId,
    messages, timeline,
    interrupt: active?.interrupt ?? null,
    patchSession, newSession, removeSession, reorderSessions,
  }
}
