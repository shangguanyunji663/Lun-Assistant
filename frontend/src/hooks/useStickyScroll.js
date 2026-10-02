import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'

/* 判定「已贴底」的容差（px）。
   留 64px：流式追加时最后一行只露出半行也视为贴底，
   否则用户正看着新 token 冒出来就被判成「离开底部」而停止跟随。 */
const BOTTOM_TOLERANCE = 64

/**
 * 对话区粘底滚动：
 * - 容器固定高度独立滚动（布局由 styles/layout.css 保证），本 hook 只管滚动位置；
 * - 贴底时（流式追加 / 内容重排）自动跟随到底；
 * - 用户向上翻阅历史时暂停跟随，不把视图拽回底部——这正是 scrollIntoView 的缺陷；
 * - 离开底部时暴露 atBottom=false，UI 可挂「回到底部」悬浮按钮；
 * - 切换会话（resetKey 变化）时复位回底部。
 *
 * 为什么用 callback ref 把元素存进 state，而不是 useRef + useEffect([])：
 *   App 首帧走 booting 分支提前 return，此时 .wb-stream 尚未挂载，ref.current 为 null；
 *   而 deps（消息条数等）在「启动态 → 已登录」两轮之间可能完全相同，
 *   依赖数组驱动的 effect 不会重跑，那一次滚动就永远丢了。
 *   实测（scripts/verify-chat-layout.mjs）表现为：布局全对，但首屏停在顶部 5000px 以外，
 *   且因 atBottom 误判为 true，「回到底部」按钮永不出现。
 *   把「元素是否已挂载」本身变成依赖，才是可靠的触发条件。
 *
 * 元素同时存一份 ref：滚动位置是纯 DOM 副作用，不该写进 state 派生出的对象，
 * 也不该被 react-hooks/immutability 规则当成「修改 state 返回值」而报错。
 *
 * @param deps   触发跟随的依赖（消息条数 / 时间线长度）
 * @param resetKey 会变化时强制复位为贴底（传会话 id）
 * @returns { scrollRef, onScroll, atBottom, scrollToBottom }
 */
export function useStickyScroll(deps, resetKey = null) {
  const [el, setEl] = useState(null)
  const elRef = useRef(null)
  const atBottomRef = useRef(true)
  const [atBottom, setAtBottom] = useState(true)

  /* 挂载 / 卸载时同步 ref 与 state */
  const attach = useCallback((node) => {
    elRef.current = node
    setEl(node)
  }, [])

  const isAtBottom = useCallback((node) => {
    if (!node) return true
    // 内容还没溢出时天然算贴底
    if (node.scrollHeight <= node.clientHeight + 1) return true
    return node.scrollHeight - node.scrollTop - node.clientHeight <= BOTTOM_TOLERANCE
  }, [])

  const syncFlag = useCallback((at) => {
    if (at === atBottomRef.current) return
    atBottomRef.current = at
    setAtBottom(at)
  }, [])

  /* 贴底状态跟随用户滚动实时更新。用 rAF 节流：拖动时滚动事件可达 60+/s，
     而 setState 会触发整棵消息树重渲染。 */
  const pending = useRef(0)
  const onScroll = useCallback(() => {
    if (pending.current) return
    pending.current = window.requestAnimationFrame(() => {
      pending.current = 0
      const node = elRef.current
      if (node) syncFlag(isAtBottom(node))
    })
  }, [isAtBottom, syncFlag])

  useEffect(() => () => {
    if (pending.current) window.cancelAnimationFrame(pending.current)
  }, [])

  const scrollToBottom = useCallback((behavior = 'auto') => {
    const node = elRef.current
    if (!node) return
    node.scrollTo({ top: node.scrollHeight, behavior })
    syncFlag(true)
  }, [syncFlag])

  /* 元素挂载后立刻贴底：首屏应直接落在最新一条上。 */
  useLayoutEffect(() => {
    const node = elRef.current
    if (!node) return
    atBottomRef.current = true
    setAtBottom(true)
    node.scrollTop = node.scrollHeight
  }, [el])

  /* 切换会话：复位为贴底。
     否则用户在上一个会话里翻历史时切过来，新会话会停在顶部——
     而那里往往是历史开头，不是「这条会话的最新一条」。 */
  const firstReset = useRef(true)
  useLayoutEffect(() => {
    if (firstReset.current) { firstReset.current = false; return }
    const node = elRef.current
    if (!node) return
    atBottomRef.current = true
    setAtBottom(true)
    node.scrollTop = node.scrollHeight
  }, [resetKey])

  /* 依赖变化时跟随：布局阶段（DOM 写入后、绘制前）调整滚动位置，
     否则每帧会先绘制一次「未滚动」的中间态，表现为消息跳动。 */
  useLayoutEffect(() => {
    const node = elRef.current
    if (!node || !atBottomRef.current) return
    node.scrollTop = node.scrollHeight
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [el, ...deps])

  /* 内容变高时同样跟随。消息区高度不只随消息条数变化：
     web 字体（Noto Serif SC 等）异步加载完成后会重排 markdown，
     图片解码、面板展开同样会改变内容高度——这些都不改 messages.length。
     观察 .wb-stream 的唯一子元素（.wb-inner），其高度即内容高度。 */
  useEffect(() => {
    const node = elRef.current
    const inner = node?.firstElementChild
    if (!node || !inner || typeof ResizeObserver === 'undefined') return
    let first = true
    const ro = new ResizeObserver(() => {
      if (!atBottomRef.current) return
      node.scrollTop = node.scrollHeight
      // 首次回调常早于字体交换完成，等一拍再校正一次
      if (first) {
        first = false
        window.requestAnimationFrame(() => {
          if (atBottomRef.current) node.scrollTop = node.scrollHeight
        })
      }
    })
    ro.observe(inner)
    return () => ro.disconnect()
  }, [el])

  return { scrollRef: attach, onScroll, atBottom, scrollToBottom }
}
