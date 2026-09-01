import React, { useEffect, useState } from 'react'
import { api } from '../api.js'
import { STATUS_LABEL } from '../constants.js'

export default function ProjectArchive({ projectId, onEdit, refreshKey }) {
  const [detail, setDetail] = useState(null)
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  const load = async () => {
    if (!projectId) { setDetail(null); return }
    setLoading(true)
    try { setDetail(await api.getProject(projectId)); setErr('') }
    catch (e) { setErr(String(e.message || e)) }
    finally { setLoading(false) }
  }
  useEffect(() => { load() }, [projectId, refreshKey])

  if (!projectId) return <p className="muted empty-tip">未关联项目。在顶部新建或选择一个论文项目后，这里会显示它的档案与结构化记忆。</p>
  if (loading) return <p className="muted empty-tip">读取中…</p>
  if (err) return <div className="err">{err}</div>
  if (!detail) return null

  const mem = detail.structured_memory || {}
  const topic = mem.topic || {}
  const outline = Array.isArray(mem.outline) ? mem.outline : []
  const facts = Array.isArray(mem.facts) ? mem.facts : []
  const progress = mem.progress || {}
  const progressKeys = Object.keys(progress)

  return (
    <div className="arch-panel">
      <div className="arch-head">
        <div>
          <div className="arch-title">{detail.title}</div>
          <div className="arch-sub">
            <span className="arch-status">{STATUS_LABEL[detail.status] || detail.status || '—'}</span>
            {detail.major && <span>{detail.major}</span>}
            <span>项目 #{detail.id}</span>
          </div>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={onEdit} title="编辑项目信息">编辑</button>
      </div>

      {detail.requirement && (
        <div className="arch-block">
          <h4 className="arch-h">写作要求</h4>
          <p className="arch-text">{detail.requirement}</p>
        </div>
      )}

      <div className="arch-block">
        <h4 className="arch-h">选题结论</h4>
        {topic.title || topic.rationale
          ? <div className="arch-text">
              {topic.title && <div className="arch-strong">{topic.title}</div>}
              {topic.rationale && <div className="muted">{topic.rationale}</div>}
            </div>
          : <p className="muted">暂无选题结论 —— 对话中确认选题后会自动沉淀。</p>}
      </div>

      <div className="arch-block">
        <h4 className="arch-h">论文大纲</h4>
        {outline.length
          ? <ol className="outline-list">
              {outline.map((o, i) => <li key={i}>{typeof o === 'string' ? o : (o.title || JSON.stringify(o))}</li>)}
            </ol>
          : <p className="muted">暂无大纲。</p>}
      </div>

      <div className="arch-block">
        <h4 className="arch-h">关键约束</h4>
        {facts.length
          ? <ul className="fact-list">{facts.map((f, i) => <li key={i}>{typeof f === 'string' ? f : JSON.stringify(f)}</li>)}</ul>
          : <p className="muted">暂无约束记录（字数、格式、交付时间等）。</p>}
      </div>

      {progressKeys.length > 0 && (
        <div className="arch-block">
          <h4 className="arch-h">章节进度</h4>
          <div className="prog-grid">
            {progressKeys.map(k => (
              <div key={k} className="prog-item">
                <span className="prog-k">{k}</span>
                <span className="prog-v">{String(progress[k])}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
