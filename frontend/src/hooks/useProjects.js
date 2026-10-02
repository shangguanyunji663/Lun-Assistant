import { useEffect, useState } from 'react'

import { api } from '../api.js'
import { toast } from '../fx.js'

/**
 * 论文项目管理：
 * - 登录后拉取项目列表；
 * - 提供 create / patch / delete 三个 CRUD 入口（返回 promise，由对话框层决定关闭时机）；
 * - archiveKey 供项目档案面板强制刷新；
 * - demo：开发预览模式下不发请求，直接用传入的 mock 项目列表。
 */
export function useProjects(user, demo = null) {
  const [projects, setProjects] = useState(demo?.projects || [])
  const [projectsErr, setProjectsErr] = useState('')
  const [projectId, setProjectId] = useState(demo?.projects?.[0]?.id ?? null)
  const [archiveKey, setArchiveKey] = useState(0)
  const [dialog, setDialog] = useState(null) // {mode:'create'|'edit', project?}

  useEffect(() => {
    if (demo) return
    if (user) {
      api.projects().then(ps => { setProjects(ps); setProjectsErr('') })
        .catch(e => {
          const msg = String(e.message || e)
          setProjectsErr(msg)
          console.warn('[projects] 加载失败:', msg)
        })
    }
  }, [user, demo])

  /* 以下三个写操作一律「显式传 id」而不是读闭包里的 projectId。
     原实现读的是渲染时快照：用户在「项目设置」弹窗打开期间
     用顶栏下拉切换了项目，PATCH/DELETE 会打到新项目上——
     改 A 的标题却写进 B，或直接删掉刚切换过去的项目。 */
  const createProject = async (title, major, requirement) => {
    if (demo) return
    const p = await api.createProject(title, major, requirement)
    setProjects(ps => [p, ...ps]); setProjectId(p.id); setProjectsErr('')
    toast('项目已创建', `#${p.id} ${p.title}`)
  }

  const patchProject = async (id, patch) => {
    if (demo) return
    if (id == null) throw new Error('未选择项目')
    await api.patchProject(id, patch)
    setProjects(ps => ps.map(p => p.id === id ? { ...p, ...patch } : p))
    setArchiveKey(k => k + 1)
  }

  const deleteProject = async (id) => {
    if (demo) return
    if (id == null) throw new Error('未选择项目')
    await api.deleteProject(id)
    setProjects(ps => ps.filter(p => p.id !== id))
    setProjectId(cur => (cur === id ? null : cur))
    setDialog(null)
  }

  const currentProject = projects.find(p => p.id === projectId) || null

  return {
    projects, projectsErr, setProjectsErr,
    projectId, setProjectId, archiveKey, setArchiveKey,
    dialog, setDialog, currentProject,
    createProject, patchProject, deleteProject,
  }
}
