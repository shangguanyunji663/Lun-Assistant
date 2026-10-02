import React, { useEffect, useState } from 'react'
import { api } from '../api.js'
import { DEMO_TRACES } from '../demo.js'

function renderTree(nodes, depth) {
  return nodes.map((n, i) => (
    <div key={i}>
      <div className="tree-row" style={{ paddingLeft: depth * 18 }}>
        <span className={`tree-kind ${n.status !== 'ok' ? 'bad' : ''}`}>{n.kind}</span>
        {n.name}
        <span className="lat"> {n.latency_ms}ms</span>
        {n.tokens_out > 0 && <span className="muted"> · out={n.tokens_out}tok</span>}
      </div>
      {n.children?.length ? renderTree(n.children, depth + 1) : null}
    </div>
  ))
}

/* 成本列格式化：后端 TraceListItem.total_cost_usd 虽声明为 float，
   但 SQL SUM 在无任何成本记录时可能给出 null（见 services/observability/trace.py），
   直接 .toFixed 会抛 TypeError 把整个面板打空。 */
const fmtCost = (v) => `$${(Number(v) || 0).toFixed(6)}`

export default function TracePanel({ demo = false }) {
  const [traces, setTraces] = useState(demo ? DEMO_TRACES : [])
  const [detail, setDetail] = useState(null)
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  const load = async () => {
    if (demo) { setTraces(DEMO_TRACES); return }
    setLoading(true)
    try { setTraces((await api.traces(30)).items || []); setErr('') }
    catch (e) { setErr(String(e.message || e)) }
    finally { setLoading(false) }
  }
  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const open = async (id) => {
    if (demo) { setErr('演示模式：未接入后端，行为回放不可用。'); return }
    /* 先清错误：否则上一次加载失败的红条会一直挂在列表上方，
       让人误以为这次的回放也失败了。 */
    setErr('')
    try { setDetail(await api.trace(id)) } catch (e) { setErr(String(e.message || e)) }
  }

  return (
    <div className="trace-panel">
      <div className="trace-list">
        <div className="panel-head">
          <h3>Trace 列表</h3>
          <button className="btn btn-ghost btn-sm" onClick={load}>刷新</button>
        </div>
        {err && <div className="err">{err}</div>}
        {traces.map(t => (
          <div key={t.trace_id} className={`trace-item ${detail?.trace_id === t.trace_id ? 'active' : ''}`}
               onClick={() => open(t.trace_id)}>
            <div className="tid">{t.trace_id.slice(0, 12)}…</div>
            <div className="meta">{t.spans} spans · {t.total_latency_ms}ms · {fmtCost(t.total_cost_usd)}</div>
          </div>
        ))}
        {loading && <p className="muted empty-tip">读取中…</p>}
        {!loading && !traces.length && <p className="muted empty-tip">暂无 Trace</p>}
      </div>
      <div className="trace-detail">
        {loading && !detail ? <p className="muted empty-tip">读取中…</p> : detail ? (
          <>
            <div className="panel-head">
              <h3>行为回放 · {detail.trace_id.slice(0, 12)}…</h3>
              <span className="muted">{detail.summary.span_count} spans · {detail.summary.total_latency_ms}ms · errors={detail.summary.error_count}</span>
            </div>
            {renderTree(detail.tree, 0)}
            <h4>时间序列</h4>
            <div className="seq">
              {detail.spans.map((s, i) => (
                <div key={i} className={`seq-row ${s.status !== 'ok' ? 'bad' : ''}`}>
                  <span className="kind">{s.kind}</span>
                  <span className="name">{s.name}</span>
                  <span className="lat">{s.latency_ms}ms</span>
                  {s.error && <span className="err-inline">{s.error}</span>}
                </div>
              ))}
            </div>
          </>
        ) : <p className="muted empty-tip">选择左侧 Trace 查看回放</p>}
      </div>
    </div>
  )
}
