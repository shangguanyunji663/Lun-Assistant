import { useCallback, useEffect, useState } from 'react'

import { DEFAULT_SKIN, LS_SKIN, SKINS, SKIN_IDS, findSkin, loadSkin, saveSkin } from '../skins/registry.js'

/**
 * v18 皮肤系统（取代 v16 的 useTheme）
 * - 把所选皮肤写入 <html data-skin>，并持久化到 localStorage.lj_skin；
 * - 监听 storage 事件，实现落地页 / 工作台 / 多标签实时联动；
 * - 同时把皮肤的主题色写进 <meta name="theme-color"> 与 color-scheme，
 *   让浏览器原生控件（滚动条、下拉框、表单）跟随皮肤明暗。
 *
 * 注：<html> 上的 data-skin 必须在首帧前就位，否则会闪一帧默认皮肤。
 *     该工作由各入口 HTML 内联脚本完成（见 index.html / app.html / landing-*.html），
 *     本 hook 只负责在 React 内部保持同步。
 */
export function useSkin() {
  const [skin, setSkinState] = useState(loadSkin)

  useEffect(() => {
    const root = document.documentElement
    root.dataset.skin = skin
    saveSkin(skin)

    const meta = findSkin(skin)
    root.style.colorScheme = ['b'].includes(skin) ? 'dark' : 'light'
    const tag = document.querySelector('meta[name="theme-color"]')
    if (tag && meta.themeColor) tag.setAttribute('content', meta.themeColor)
  }, [skin])

  /* 跨页 / 跨标签联动：落地页切了皮肤，工作台同步 */
  useEffect(() => {
    const onStorage = (e) => {
      if (e.key === LS_SKIN && SKIN_IDS.includes(e.newValue)) setSkinState(e.newValue)
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  const setSkin = useCallback((id) => {
    if (SKIN_IDS.includes(id)) setSkinState(id)
  }, [])

  return { skin, setSkin, skins: SKINS, defaultSkin: DEFAULT_SKIN }
}