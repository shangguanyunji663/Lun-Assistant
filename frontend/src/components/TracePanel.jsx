import React, { useEffect, useState } from 'react'
import { api } from '../api.js'

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

export default function TracePanel() {
  const [traces, setTraces] = useState([])
  const [detail, setDetail] = useState(null)
  const [err, setErr] = useState('')

  const load = async () => {
    try { setTraces((await api.traces(30)).items); setErr('') } catch (e) { setErr(String(e.message || e)) }
  }
  useEffect(() => { load() }, [])

  const open = async (id) => {
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
            <div className="meta">{t.spans} spans · {t.total_latency_ms}ms · ${t.total_cost_usd.toFixed(6)}</div>
          </div>
        ))}
        {!traces.length && <p className="muted empty-tip">暂无 Trace</p>}
      </div>
      <div className="trace-detail">
        {detail ? (
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
