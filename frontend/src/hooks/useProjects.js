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

  const createProject = async (title, major, requirement) => {
    if (demo) return
    const p = await api.createProject(title, major, requirement)
    setProjects(ps => [p, ...ps]); setProjectId(p.id); setProjectsErr('')
    toast('项目已创建', `#${p.id} ${p.title}`)
  }

  const patchProject = async (patch) => {
    if (demo) return
    await api.patchProject(projectId, patch)
    setProjects(ps => ps.map(p => p.id === projectId ? { ...p, ...patch } : p))
    setArchiveKey(k => k + 1)
  }

  const deleteProject = async () => {
    if (demo) return
    await api.deleteProject(projectId)
    setProjects(ps => ps.filter(p => p.id !== projectId))
    setProjectId(null); setDialog(null)
  }

  const currentProject = projects.find(p => p.id === projectId) || null

  return {
    projects, projectsErr, setProjectsErr,
    projectId, setProjectId, archiveKey, setArchiveKey,
    dialog, setDialog, currentProject,
    createProject, patchProject, deleteProject,
  }
}
