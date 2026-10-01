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
      msgs: [...s.msgs, { role: 'user', content: body, ts: Date.now() }],
    }))
    // 占位助手消息
    patchSession(sid, s => ({ ...s, msgs: [...s.msgs, { role: 'assistant', content: '', ts: Date.now() }] }))

    // 只替换 content，保留该消息的 ts（供 ops 主题显示等宽时间戳）
    const patchLast = (content) =>
      patchSession(sid, s => {
        if (!s.msgs.length) return s
        const c = [...s.msgs]
        c[c.length - 1] = { ...c[c.length - 1], content }
        return { ...s, msgs: c }
      })

    /* ---- v17 打字机平滑层 ----
       SSE 的 token 到达节奏不均匀（有时整段一次性到达），直接回填会「跳字」。
       这里把已收到的全文缓存在 target，按固定节拍匀速揭示；落后越多步长越大，
       保证长回答不会拖尾太久。streaming 结束时立即补齐剩余全文。 */
    let target = ''
    let revealed = 0
    let typer = 0
    const TICK_MS = 24
    const stopTyper = () => { if (typer) { window.clearInterval(typer); typer = 0 } }
    const startTyper = () => {
      if (typer) return
      typer = window.setInterval(() => {
        if (revealed >= target.length) { stopTyper(); return }
        const step = Math.max(1, Math.ceil((target.length - revealed) / 16))
        revealed = Math.min(target.length, revealed + step)
        patchLast(target.slice(0, revealed))
      }, TICK_MS)
    }
    const feedTyper = (chunk) => {
      target += chunk
      startTyper()
    }
    const flushTyper = () => {
      stopTyper()
      if (target) { revealed = target.length; patchLast(target) }
    }

    try {
      const finalText = await sse(resume ? '/agent/resume' : '/agent/chat',
        resume
          ? { session_id: sid, feedback: resume, project_id: projectId }
          : { session_id: sid, message: text, project_id: projectId },
        (type, payload, node) => {
          if (type === 'token') { feedTyper(payload || '') }
          else if (type === 'final') { if (payload?.output) { target = payload.output; startTyper() } }
          else if (type === 'interrupt') {
            setInterrupt(payload)
            patchSession(sid, s => ({ ...s, timeline: [...s.timeline, { type: 'interrupt', payload, node }] }))
          } else if (type === 'error') {
            patchSession(sid, s => ({ ...s, timeline: [...s.timeline, { type: 'error', payload, node }] }))
          } else if (['node_start', 'node_end', 'intent', 'route', 'plan', 'step_event'].includes(type)) {
            patchSession(sid, s => ({ ...s, timeline: [...s.timeline, { type, payload, node }] }))
          }
        })
      if (finalText) target = finalText
      flushTyper()
      if (projectId) setArchiveKey(k => k + 1)
    } catch (e) {
      stopTyper()
      patchLast(`请求失败：${e.message || e}`)
      console.warn('[chat]', e)
    } finally { stopTyper(); setStreaming(false) }
  }

  return { streaming, interrupt, setInterrupt, input, setInput, send }
}
