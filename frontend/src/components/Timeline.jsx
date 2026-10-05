/* ============================================================
   执行时间线 · v18
     数据源不变（后端 node_start / node_end / intent / route / plan /
     step_event / interrupt / error 事件），仅把标记换成皮肤契约里的
     .wb-tl-* 语义类，让八套设计语言各自排版。
   ============================================================ */

const LABEL = {
  node_start: (p) => ({ kind: 'start', text: p?.title || p?.agent || 'Agent', meta: '开始' }),
  node_end: (p, node) => ({
    kind: 'end',
    text: p?.title || p?.agent || node || '',
    meta: p?.stop_reason === 'max_hops' ? '已完成 · 达到最大跳数' : '已完成',
  }),
  intent: (p) => ({ kind: 'intent', text: `意图 · ${p?.label ?? '—'}`, meta: `${p?.layer ?? ''} · conf ${p?.confidence ?? '—'}` }),
  route: (p) => ({ kind: 'route', text: `路由至 ${p?.next ?? '—'}`, meta: 'route' }),
  plan: (p) => ({ kind: 'plan', text: `规划 · ${p?.goal?.slice(0, 40) || '—'}`, meta: `${p?.steps?.length || 0} 步` }),
  step_event: (p) => {
    /* 两种来源：planner 的计划步骤（step/total）与专项节点的工具调用进度
       （tool + status: running/ok/error + elapsed_s）。 */
    const text = p?.tool
      ? (p?.action || p?.tool)
      : `步骤 ${p?.step ?? '—'}/${p?.total ?? '—'} ${p?.action ?? ''}`
    const meta = p?.status === 'ok'
      ? (p?.elapsed_s != null ? `完成 · ${p.elapsed_s}s` : '完成')
      : (p?.status === 'running' ? '进行中' : '异常')
    return { kind: 'step', text, meta }
  },
  interrupt: (p) => ({ kind: 'interrupt', text: '待确认', meta: p?.question || '需要你的决定' }),
  error: (p) => ({ kind: 'error', text: '错误', meta: p?.message || '—' }),
}

export default function Timeline({ events, turnOf, onJump }) {
  if (!events.length) return null
  return (
    <ol className="wb-tl">
      {events.map((ev, i) => {
        const make = LABEL[ev.type]
        if (!make) return null
        const d = make(ev.payload, ev.node)
        /* turnOf[i] ≥ 0 表示推断出了对应的 assistant 消息，可点击跳转；
           -1（无消息可锚定）保持纯展示，不给手势也不给焦点。 */
        const target = turnOf?.[i] ?? -1
        const clickable = target >= 0 && typeof onJump === 'function'
        return (
          <li key={i}
              className={`wb-tl-item is-${d.kind}${clickable ? ' is-clickable' : ''}`}
              role={clickable ? 'button' : undefined}
              tabIndex={clickable ? 0 : undefined}
              aria-label={clickable ? `跳转到对应的回答消息` : undefined}
              title={clickable ? '点击跳转到这条事件对应的回答' : undefined}
              onClick={clickable ? () => onJump(i) : undefined}
              onKeyDown={clickable ? (e => {
                if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onJump(i) }
              }) : undefined}>
            <span className="wb-tl-no" aria-hidden="true">{String(i + 1).padStart(2, '0')}</span>
            <span className="wb-tl-body">
              <span className="wb-tl-title">{d.text}</span>
              <span className="wb-tl-meta">{d.meta}</span>
            </span>
          </li>
        )
      })}
    </ol>
  )
}