import { useCallback, useRef, useState } from 'react'

import { sse } from '../api.js'
import { DEMO_INTERRUPT, demoReply } from '../demo.js'
import { titleOf } from './useSessions.js'

/* 演示模式应答：按固定节奏把假文本喂给打字机，并补一条时间线与中断，
   让「流式观感 / 时间线 / 中断确认条」三处在不起后端时也能被验证。
   注：demo.js 用静态引入（App.jsx 也静态引它，动态 import 反而拆不出 chunk）。 */
async function demoChat(sid, text, resume, { feedTyper, patchSession, setInterrupt }) {
  const out = demoReply(resume || text)
  patchSession(sid, s => ({
    ...s,
    timeline: [...s.timeline, {
      type: 'intent',
      payload: { label: resume ? '人工确认反馈' : '演示请求', layer: 'demo', confidence: 0.99 },
    }],
  }))
  for (const c of (out.match(/[\s\S]{1,6}/g) || [])) {
    feedTyper(c)
    await new Promise(r => setTimeout(r, 26))
  }
  setInterrupt(DEMO_INTERRUPT)
  patchSession(sid, s => ({
    ...s,
    interrupt: DEMO_INTERRUPT,
    timeline: [...s.timeline, { type: 'interrupt', payload: DEMO_INTERRUPT }],
  }))
  return out
}

/**
 * 对话发送与 SSE 流式编排：
 * - 追加用户消息 / 占位助手消息；
 * - 通过 patchSession 增量更新当前流式文本、时间线事件；
 * - interrupt 中断态由调用方展示"确认条"，resume 续跑复用 send；
 * - demo（开发预览）：不发请求，用固定的应答文本走同一条打字机管线，
 *   以便在不起后端的情况下验证六套皮肤下的流式观感。
 */
export function useChat({ active, patchSession, projectId, setArchiveKey, demo = null }) {
  const [streaming, setStreaming] = useState(false)
  const [input, setInput] = useState('')
  /* 重入锁：send 是 async，streaming 是 render 闭包里的快照。
     连按两次「发送」时两次调用读到的都是同一个 false，
     会并发开两条 SSE 流并往同一条消息里交叉写入。ref 是同步的，可作闸门。 */
  const inFlight = useRef(false)

  /* interrupt（待确认项）按会话存放，不再是全局单值。
     原实现挂在 hook 级 state 上：会话 A 挂起后切到 B，
     setInterrupt(null) 会把 A 的待确认项一起抹掉——而后端图仍停在
     interrupt 节点等待 resume，切回去已无任何入口，链路就此卡死。
     存进会话对象后，它随会话走，切换与刷新都不丢。 */
  const interrupt = active?.interrupt ?? null
  const setInterrupt = useCallback((value) => {
    const sid = active?.id
    if (!sid) return
    patchSession(sid, s => ({ ...s, interrupt: value }))
  }, [active?.id, patchSession])

  const send = async (text, resume = null) => {
    if (inFlight.current || !active) return
    const sid = active.id
    const body = resume ? `[确认反馈] ${resume}` : text

    inFlight.current = true
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
      const finalText = demo
        ? await demoChat(sid, text, resume, { feedTyper, patchSession, setInterrupt })
        : await sse(resume ? '/agent/resume' : '/agent/chat',
        resume
          ? { session_id: sid, feedback: resume, project_id: projectId }
          : { session_id: sid, message: text, project_id: projectId },
        (type, payload, node) => {
          if (type === 'token') { feedTyper(payload || '') }
          else if (type === 'final') {
            /* final.output 用来兜底「token 丢帧」的情况。
               只有当它比我们已收到的更长时才采纳——否则会把已上屏的
               内容截断成最后一个节点的 final_output（多智能体场景）。 */
            const out = payload?.output
            if (out && out.length > target.length) { target = out; startTyper() }
          }
          else if (type === 'interrupt') {
            setInterrupt(payload)
            /* 专项节点走非流式 chat_tools，挂起前不会下发任何 token，
               占位助手消息会留成空泡。把待确认内容写进气泡，
               用户不必只盯着下方确认条才知道 agent 说了什么。 */
            if (!target.trim()) {
              const proposal = payload?.proposal
              const question = payload?.question || '请确认下一步操作'
              target = proposal ? `${question}\n\n${proposal}` : question
              startTyper()
            }
            patchSession(sid, s => ({
              ...s,
              interrupt: payload,
              timeline: [...s.timeline, { type: 'interrupt', payload, node }],
            }))
          } else if (type === 'error') {
            /* error 事件后没有 final，占位消息会留空；
               直接把后端 message 写进气泡，避免「什么都没有」。 */
            target = `请求出错：${payload?.message || '未知错误'}`
            startTyper()
            patchSession(sid, s => ({ ...s, timeline: [...s.timeline, { type: 'error', payload, node }] }))
          } else if (['node_start', 'node_end', 'intent', 'route', 'plan', 'step_event'].includes(type)) {
            patchSession(sid, s => ({ ...s, timeline: [...s.timeline, { type, payload, node }] }))
          }
        })
      if (finalText && finalText.length > target.length) target = finalText
      flushTyper()
      if (projectId) setArchiveKey(k => k + 1)
    } catch (e) {
      stopTyper()
      patchLast(`请求失败：${e.message || e}`)
      console.warn('[chat]', e)
    } finally {
      stopTyper()
      /* 流已结束但一条 token 都没收到（例如后端直接判定挂起或出错）：
         占位助手消息会是空的，补一句说明而不是留白泡。 */
      if (!target.trim()) patchLast('（本轮没有产出内容）')
      inFlight.current = false
      setStreaming(false)
    }
  }

  return { streaming, interrupt, setInterrupt, input, setInput, send }
}
