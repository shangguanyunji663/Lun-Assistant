import React from 'react'

// 节点中文名直接取后端 node_start/node_end 事件 payload.title（specs.py SpecialistSpec.title
// 与 planner/supervisor 内的 title），前端不再维护重复映射。
export default function Timeline({ events }) {
  if (!events.length) return null
  return (
    <div className="timeline">
      {events.map((ev, i) => (
        <div key={i} className={`tl-item tl-${ev.type}`}>
          {ev.type === 'node_start' && <span className="tl-tag start">▶ {ev.payload?.title || ev.payload?.agent || 'Agent'}</span>}
          {ev.type === 'intent' && <span className="tl-tag intent">意图 · {ev.payload?.label}（{ev.payload?.layer}，conf={ev.payload?.confidence}）</span>}
          {ev.type === 'route' && <span className="tl-tag route">→ 路由至 {ev.payload?.next}</span>}
          {ev.type === 'plan' && <span className="tl-tag plan">规划 · {ev.payload?.goal?.slice(0, 40) || ''} · {ev.payload?.steps?.length || 0} 步</span>}
          {ev.type === 'step_event' && <span className="tl-tag step">步骤 {ev.payload?.step}/{ev.payload?.total} {ev.payload?.action}{ev.payload?.status === 'ok' ? ' ✓' : ' ⚠'}</span>}
          {ev.type === 'node_end' && <span className="tl-tag end">✔ {ev.payload?.title || ev.payload?.agent || ev.node || ''} 完成{ev.payload?.stop_reason === 'max_hops' ? '（达到最大跳数）' : ''}</span>}
          {ev.type === 'interrupt' && <span className="tl-tag interrupt">⏸ 待确认 · {ev.payload?.question || JSON.stringify(ev.payload)}</span>}
          {ev.type === 'error' && <span className="tl-tag err">✖ {ev.payload?.message}</span>}
        </div>
      ))}
    </div>
  )
}
