import { useEffect, useRef, useState } from 'react'

const LS_KEY = 'lj_sessions_v1'
const MAX_SESSIONS = 30

const makeId = () => `web-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`

/** 会话标题：取首条用户消息前 18 字 */
export const titleOf = (text) => {
  const t = String(text || '').replace(/\s+/g, ' ').trim()
  return t ? (t.length > 18 ? t.slice(0, 18) + '…' : t) : '新会话'
}

const emptySession = () => ({ id: makeId(), title: '新会话', msgs: [], timeline: [], updatedAt: Date.now() })

const loadSessions = () => {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (!raw) return []
    const list = JSON.parse(raw)
    return Array.isArray(list) ? list.filter(s => s && s.id) : []
  } catch { return [] }
}

/**
 * 多会话卷册管理：
 * - 会话列表 / 当前会话，localStorage 持久化（上限 MAX_SESSIONS）；
 * - 保证至少存在一个会话；patchSession 供 SSE 增量更新会话内容。
 */
export function useSessions() {
  const [sessions, setSessions] = useState(loadSessions)
  const [activeId, setActiveId] = useState(null)
  const bottomRef = useRef(null)

  /* 确保至少有一个会话 */
  useEffect(() => {
    if (!sessions.length) {
      const s = emptySession()
      setSessions([s]); setActiveId(s.id)
    } else if (!sessions.some(s => s.id === activeId)) {
      setActiveId(sessions[0].id)
    }
  }, [sessions, activeId])

  /* 持久化 */
  useEffect(() => {
    try { localStorage.setItem(LS_KEY, JSON.stringify(sessions.slice(0, MAX_SESSIONS))) } catch { /* 隐私模式忽略 */ }
  }, [sessions])

  const patchSession = (id, fn) =>
    setSessions(list => list.map(s => (s.id === id ? { ...fn(s), updatedAt: Date.now() } : s)))

  const newSession = () => {
    const s = emptySession()
    setSessions(list => [s, ...list].slice(0, MAX_SESSIONS))
    setActiveId(s.id)
  }

  const removeSession = (id) => {
    setSessions(list => {
      const rest = list.filter(s => s.id !== id)
      if (rest.length) {
        if (id === activeId) setActiveId(rest[0].id)
        return rest
      }
      const s = emptySession()
      setActiveId(s.id)
      return [s]
    })
  }

  const active = sessions.find(s => s.id === activeId) || sessions[0] || null
  const messages = active?.msgs ?? []
  const timeline = active?.timeline ?? []

  return {
    sessions, active, activeId, setActiveId,
    messages, timeline, bottomRef,
    patchSession, newSession, removeSession,
  }
}
