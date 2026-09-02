import { useState } from 'react'

import { sse } from '../api.js'
import { titleOf } from './useSessions.js'

/**
 * 对话发送与 SSE 流式编排：
 * - 追加用户消息 / 占位助手消息；
 * - 通过 patchSession 增量更新当前流式文本、时间线事件；
 * - interrupt 中断态由调用方展示"确认条"，resume 续跑复用 send。
 */
export function useChat({ active, patchSession, projectId, setArchiveKey }) {
  const [streaming, setStreaming] = useState(false)
  const [interrupt, setInterrupt] = useState(null)
  const [input, setInput] = useState('')

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

  return { streaming, interrupt, setInterrupt, input, setInput, send }
}
