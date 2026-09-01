const API = '/api'

async function req(path, options = {}) {
  const token = localStorage.getItem('lj_token')
  const res = await fetch(API + path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  })
  if (res.status === 401) { localStorage.removeItem('lj_token'); window.location.reload() }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `${res.status}`)
  }
  return res.json()
}

export const api = {
  register: (username, password) => req('/auth/register', { method: 'POST', body: JSON.stringify({ username, password }) }),
  login: (username, password) => req('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
  me: () => req('/auth/me'),
  projects: () => req('/projects'),
  createProject: (title, major, requirement) => req('/projects', { method: 'POST', body: JSON.stringify({ title, major, requirement }) }),
  deleteProject: (id) => req(`/projects/${id}`, { method: 'DELETE' }),

  // ---- 项目级知识库（第 4 轮上线）----
  uploadKnowledge: async (projectId, files) => {
    const fd = new FormData()
    files.forEach(f => fd.append('files', f, f.name))
    const res = await fetch(`${API}/projects/${projectId}/knowledge`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('lj_token')}` }, // 不设 Content-Type，由浏览器生成 boundary
      body: fd,
    })
    if (res.status === 401) { localStorage.removeItem('lj_token'); window.location.reload() }
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || `${res.status}`)
    }
    return res.json()
  },
  listKnowledge: (projectId) => req(`/projects/${projectId}/knowledge`),
  deleteKnowledge: (projectId, docId) => req(`/projects/${projectId}/knowledge/${docId}`, { method: 'DELETE' }),
  searchKnowledge: (projectId, query, top_k = 5, mode = 'hybrid') =>
    req(`/projects/${projectId}/knowledge/search`, { method: 'POST', body: JSON.stringify({ query, top_k, mode }) }),

  traces: (limit = 30) => req(`/observability/traces?limit=${limit}`),
  trace: (id) => req(`/observability/traces/${id}`),
}

/** SSE 流式请求：onEvent(type, payload, node) 回调；返回 final 文本。 */
export async function sse(path, body, onEvent) {
  const token = localStorage.getItem('lj_token')
  const res = await fetch(API + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const eb = await res.json().catch(() => ({}))
    throw new Error(eb.detail || `${res.status}`)
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''
  let finalText = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    let idx
    while ((idx = buf.indexOf('\n\n')) >= 0) {
      const raw = buf.slice(0, idx).trim()
      buf = buf.slice(idx + 2)
      if (!raw.startsWith('data:')) continue
      try {
        const ev = JSON.parse(raw.slice(5).trim())
        onEvent?.(ev.type, ev.payload, ev.node)
        if (ev.type === 'final') finalText = ev.payload?.output || ''
      } catch { /* 忽略坏帧 */ }
    }
  }
  return finalText
}
