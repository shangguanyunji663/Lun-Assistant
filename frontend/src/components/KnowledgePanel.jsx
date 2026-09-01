import React, { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'

const FMT_ICON = { pdf: 'PDF', docx: 'DOC', txt: 'TXT', md: 'MD' }

// 文档状态徽章（后端 ingest pipeline 仅产出 ready / parsing / failed）
function StatusBadge({ status }) {
  const label = { ready: '已入库', parsing: '解析中', failed: '失败' }[status] || status
  return <span className={`kb-status kb-status-${status}`}>{label}</span>
}

export default function KnowledgePanel({ projectId }) {
  const [docs, setDocs] = useState([])
  const [err, setErr] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState('')
  const [summary, setSummary] = useState(null)
  const [q, setQ] = useState('')
  const [mode, setMode] = useState('hybrid')
  const [hits, setHits] = useState(null)
  const [fallback, setFallback] = useState(false)
  const [searching, setSearching] = useState(false)
  const fileRef = useRef(null)

  const load = async (pid = projectId) => {
    if (!pid) { setDocs([]); return }
    try { setDocs((await api.listKnowledge(pid)).documents); setErr('') }
    catch (e) { setErr(String(e.message || e)) }
  }
  useEffect(() => { load(); setHits(null); setUploadMsg('') }, [projectId])

  const upload = async (files) => {
    const arr = Array.from(files || [])
    if (!arr.length || uploading) return
    setUploading(true); setUploadMsg(''); setErr('')
    try {
      const r = await api.uploadKnowledge(projectId, arr)
      setSummary(r)
      setUploadMsg(r.ready > 0 ? `已入库 ${r.ready}/${arr.length} 份` : `本次 ${arr.length} 份均未入库`)
    } catch (e) { setErr(String(e.message || e)) }
    finally { setUploading(false); setHits(null); load() }
    fileRef.current && (fileRef.current.value = '')
  }

  const remove = async (docId, filename) => {
    if (!window.confirm(`确定从知识库删除「${filename}」？对应向量分块与原始文件将一并清除。`)) return
    try { await api.deleteKnowledge(projectId, docId); setErr(''); load(); setHits(null) }
    catch (e) { setErr(String(e.message || e)) }
  }

  const search = async () => {
    const query = q.trim()
    if (!query || searching) return
    setSearching(true); setErr(''); setFallback(false)
    try {
      let results = (await api.searchKnowledge(projectId, query, 5, mode)).results
      if (mode === 'project' && !results.length) {
        results = (await api.searchKnowledge(projectId, query, 5, 'hybrid')).results
        setFallback(true)
      }
      setHits(results)
    } catch (e) { setErr(String(e.message || e)) }
    finally { setSearching(false) }
  }

  return (
    <div className="kb-panel">
      {!projectId && <p className="muted empty-tip">请先在顶部选择或新建论文项目，再上传你的参考资料。</p>}

      {projectId && (<>
        <div className="kb-drop"
             onClick={() => fileRef.current?.click()}
             onDragOver={e => e.preventDefault()}
             onDrop={e => { e.preventDefault(); upload(e.dataTransfer.files) }}
             onKeyDown={e => e.key === 'Enter' && fileRef.current?.click()}
             role="button" tabIndex={0}>
          <input ref={fileRef} type="file" multiple hidden
                 accept=".pdf,.docx,.txt,.md,.markdown"
                 onChange={e => upload(e.target.files)} />
          <div className="kb-drop-icon">{uploading ? '入' : '＋'}</div>
          <div className="kb-drop-main">{uploading ? '解析入库中…（分块 + 向量化）' : '点击或拖拽上传资料'}</div>
          <div className="muted">PDF / DOCX / TXT / MD ｜ 单文件 ≤20MB ｜ 同内容自动去重</div>
        </div>

        {uploadMsg && (
          <div className="kb-upload-msg">
            <span>{uploadMsg}</span>
            {summary?.results?.map((r, i) => (
              <span key={i} className={`kb-mini kb-mini-${r.status}`}>
                {r.status === 'ready' ? '✓' : r.status === 'skipped' ? '＝' : '✕'} {r.filename}
              </span>
            ))}
          </div>
        )}
        {err && <div className="err">{err}</div>}

        <div className="kb-search">
          <input placeholder="库内检索：如 RRF 倒数排名融合…" value={q}
                 onChange={e => setQ(e.target.value)}
                 onKeyDown={e => { if (e.key === 'Enter') search() }} />
          <select value={mode} onChange={e => setMode(e.target.value)} title="检索范围（v10 三态：仅内置 / 仅库内 / 混合）">
            <option value="hybrid">混合</option>
            <option value="builtin">仅内置</option>
            <option value="project">仅库内</option>
          </select>
          <button className="btn btn-ink" onClick={search} disabled={searching || !q.trim()}>{searching ? '…' : '检索'}</button>
        </div>

        {hits !== null && (
          <div className="kb-hits">
            <div className="panel-head"><h3>{hits.length ? '检索命中' : '未命中'}</h3>
              <span className="muted link" onClick={() => setHits(null)}>收起</span></div>
            {fallback && !hits.length &&
              <p className="muted empty-tip">库内无命中，已自动检索公共语料（把右侧模式切回「混合」即可默认合并检索）。</p>}
            {fallback && hits.length > 0 &&
              <div className="kb-fallback-tip">库内未命中，已为你检索公共语料（混合模式）</div>}
            {hits.map((h, i) => (
              <div key={i} className="kb-hit">
                <div className="kb-hit-head">
                  <span className="kh-src">{h.doc_id ? '知识库' : '公共语料'}</span>
                  <span className="kh-score">{h.score}</span>
                  {h.noise_flag !== 'ok' && <span className={`kb-mini kb-mini-${h.noise_flag === 'sparse_only' ? 'failed' : 'weak'}`}>{h.noise_flag}</span>}
                </div>
                <div className="kh-name">{h.filename || h.source || '(文档)'}</div>
                <div className="kh-content">{h.content}</div>
              </div>
            ))}
          </div>
        )}

        <div className="kb-docs">
          <div className="panel-head"><h3>资料清单 {docs.length ? `（${docs.length}）` : ''}</h3></div>
          {!docs.length && <p className="muted empty-tip">尚未上传资料：把论文相关的 PDF、笔记、课件放进来，对话检索会优先引用它们。</p>}
          {docs.map(d => (
            <div key={d.id} className={`kb-doc ${d.status !== 'ready' ? 'kb-doc-bad' : ''}`}>
              <div className="kd-icon">{FMT_ICON[d.file_type] || 'DOC'}</div>
              <div className="kd-body">
                <div className="kd-name" title={d.filename}>{d.filename}</div>
                <div className="kd-meta">
                  <StatusBadge status={d.status} />
                  {d.chunk_count > 0 && <span>{d.chunk_count} 分块</span>}
                  {d.word_count > 0 && <span>{d.word_count.toLocaleString()} 字</span>}
                </div>
                {d.error && <div className="kd-err">{d.error}</div>}
              </div>
              {d.status === 'ready' && (
                <button className="kd-del" title="删除" onClick={() => remove(d.id, d.filename)}>✕</button>
              )}
            </div>
          ))}
        </div>
      </>)}
    </div>
  )
}
