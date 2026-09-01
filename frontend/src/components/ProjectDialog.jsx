import React, { useState } from 'react'
import { BrushRule } from './decor.jsx'

// 项目弹窗 —— 新建（POST）与 编辑/删除（PATCH / DELETE）
// 状态选项与后端 infrastructure/models/project.py PROJECT_STATUSES 一致
const STATUS_OPTIONS = [
  ['created', '立项'], ['topic', '选题中'], ['literature', '文献阶段'],
  ['writing', '写作阶段'], ['review', '校验阶段'], ['finalize', '已定稿'],
]

export default function ProjectDialog({ mode, initial, onClose, onCreate, onPatch, onDelete }) {
  const [title, setTitle] = useState(initial?.title || '')
  const [major, setMajor] = useState(initial?.major || '')
  const [requirement, setRequirement] = useState(initial?.requirement || '')
  const [status, setStatus] = useState(initial?.status || 'created')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  const editing = mode === 'edit'

  const submit = async () => {
    const t = title.trim()
    if (!t) return
    setBusy(true); setErr('')
    try {
      if (editing) await onPatch({ title: t, major: major.trim(), requirement: requirement.trim(), status })
      else await onCreate(t, major.trim(), requirement.trim())
      onClose()
    } catch (e) { setErr(String(e.message || e)) }
    finally { setBusy(false) }
  }

  const doDelete = async () => {
    if (!window.confirm(`确定删除项目「${initial?.title || ''}」？其下的知识库文档与结构化记忆将一并移除，且不可恢复。`)) return
    setBusy(true); setErr('')
    try { await onDelete() } catch (e) { setErr(String(e.message || e)); setBusy(false) }
  }

  return (
    <div className="modal-mask" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="modal-card" onClick={e => e.stopPropagation()}>
        <h3>{editing ? '编辑论文项目' : '新建论文项目'}</h3>
        <div className="modal-rule"><BrushRule width={80} /></div>
        {!editing && <p className="muted center">先给论文起一个题目，专业与写作要求可稍后补充。</p>}

        <div className="field">
          <label>论文题目</label>
          <input autoFocus placeholder="例如：基于 LangGraph 的多智能体论文助手" value={title}
                 onChange={e => setTitle(e.target.value)}
                 onKeyDown={e => { if (e.key === 'Enter' && title.trim()) submit() }} />
        </div>
        {editing && (<>
          <div className="field">
            <label>专业方向</label>
            <input placeholder="例如：计算机科学与技术" value={major} onChange={e => setMajor(e.target.value)} />
          </div>
          <div className="field">
            <label>写作要求</label>
            <textarea rows={3} placeholder="字数、格式、交付节点等约束" value={requirement}
                      onChange={e => setRequirement(e.target.value)} />
          </div>
          <div className="field">
            <label>项目状态</label>
            <select value={status} onChange={e => setStatus(e.target.value)}>
              {STATUS_OPTIONS.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
            </select>
          </div>
        </>)}

        {err && <div className="err">{err}</div>}

        <div className="modal-actions">
          {editing && <button className="btn btn-danger btn-sm" onClick={doDelete} disabled={busy}>删除项目</button>}
          <span style={{ flex: 1 }} />
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>取消</button>
          <button className="btn btn-ink" onClick={submit} disabled={busy || !title.trim()}>
            {editing ? '保存' : '创建'}
          </button>
        </div>
      </div>
    </div>
  )
}
