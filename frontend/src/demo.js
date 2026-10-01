/* ============================================================
   v18 · 开发预览数据（仅 DEV 构建可用）
   —— 用途：六套皮肤的视觉联调。工作台依赖后端（FastAPI + PostgreSQL +
      Redis + Ollama）才能登录并产生真实数据，而「换一套设计语言要重新
      起一遍全套服务」的代价过高，故提供一份纯前端 mock。
     启动方式：npm run dev 后访问 http://localhost:5173/app.html?demo=1

   生产构建下 DEV 为 false，Vite 会把 `DEV ? <字面量> : <空值>` 折叠成空值，
   死代码连带这些 mock 数据一起被移除——产物里不会出现演示内容。
   ============================================================ */

const DEV = import.meta.env.DEV

export function isDemo() {
  if (!DEV) return false
  try {
    return new URLSearchParams(window.location.search).has('demo')
  } catch {
    return false
  }
}

export const DEMO_USER = DEV ? { username: '吕江', role: 'admin' } : null

export const DEMO_PROJECTS = DEV ? [
  { id: 12, title: '大模型辅助的文献综述自动化研究', major: '计算机科学与技术', status: 'writing' },
  { id: 11, title: '面向古籍整理的大模型辅助校勘研究', major: '中国语言文学', status: 'literature' },
] : []

export const DEMO_ARCHIVE = DEV ? {
  id: 12,
  title: '大模型辅助的文献综述自动化研究',
  major: '计算机科学与技术',
  status: 'writing',
  requirement: '正文不少于 1.8 万字；引用格式 GB/T 7714；第三章需含实验设计与信效度检验。',
  structured_memory: {
    topic: {
      title: 'RAG 评测鲁棒性',
      rationale: '数据可控、实验可复现，三类扰动（对抗查询 / 检索失败 / 引用幻觉）清晰可测。',
    },
    outline: [
      '第一章 绪论：研究背景、问题定义与贡献',
      '第二章 相关工作：RAG 管线与评测方法',
      '第三章 方法论：扰动构造与鲁棒性度量',
      '第四章 实验：基准对比与消融',
      '第五章 结论与展望',
    ],
    facts: ['正文字数 ≥ 18000', '引用格式 GB/T 7714', '第三章须含信效度检验'],
    progress: { 第一章: '草稿完成', 第二章: '草稿完成', 第三章: '待采纳', 第四章: '未开始' },
  },
} : null

export const DEMO_KNOWLEDGE = DEV ? [
  { id: 1, filename: '综述_2024.pdf', file_type: 'pdf', status: 'ready', chunk_count: 128, word_count: 24180 },
  { id: 2, filename: '实验记录.md', file_type: 'md', status: 'ready', chunk_count: 34, word_count: 6820 },
  { id: 3, filename: '开题报告.docx', file_type: 'docx', status: 'parsing', chunk_count: 0, word_count: 0 },
] : []

export const DEMO_TRACES = DEV ? [
  { trace_id: 'tr_9f3a1c8e2b47', spans: 9, total_latency_ms: 4180, total_cost_usd: 0.000412 },
  { trace_id: 'tr_5c71d0a49e33', spans: 6, total_latency_ms: 2260, total_cost_usd: 0.000188 },
] : []

const now = Date.now()

export const DEMO_SESSIONS = DEV ? [
  {
    id: 'demo-1',
    title: '选题方向探索',
    updatedAt: now - 60000,
    msgs: [
      { role: 'user', content: '帮我确定一个可行的论文选题，大模型方向，要能做出实验。', ts: now - 180000 },
      {
        role: 'assistant',
        ts: now - 170000,
        content: [
          '建议从「RAG 评测鲁棒性」切入。理由有三：',
          '',
          '1. 数据可控、实验可复现；',
          '2. 三类扰动清晰可测——**对抗查询**、检索失败、引用幻觉；',
          '3. 近三年基准论文充足。',
          '',
          '已调度文献环节拉取 50 篇核心论文，选题结论待你确认后写入项目档案。',
        ].join('\n'),
      },
    ],
    timeline: [
      { type: 'intent', payload: { label: '选题咨询', layer: 'rule+lexical', confidence: 0.96 } },
      { type: 'plan', payload: { goal: '确定选题并沉淀为项目档案', steps: [{}, {}, {}] } },
      { type: 'node_start', payload: { title: '文献检索' } },
      { type: 'step_event', payload: { step: 1, total: 3, action: '三路召回 + RRF 融合', status: 'ok' } },
      { type: 'node_end', payload: { title: '文献检索', stop_reason: 'ok' } },
      { type: 'interrupt', payload: { question: '第三章方法论初稿已生成，是否采纳？', options: ['采纳', '修改后采纳', '重新生成'] } },
    ],
  },
  {
    id: 'demo-2',
    title: '文献检索',
    updatedAt: now - 26 * 3600000,
    msgs: [{ role: 'user', content: '检索近三年大模型相关文献', ts: now - 26 * 3600000 }],
    timeline: [],
  },
  {
    id: 'demo-3',
    title: '方法论初稿',
    updatedAt: now - 3 * 86400000,
    msgs: [{ role: 'user', content: '为第三章写一段方法论初稿', ts: now - 3 * 86400000 }],
    timeline: [],
  },
  {
    id: 'demo-4',
    title: '格式规范核对',
    updatedAt: now - 7 * 86400000,
    msgs: [{ role: 'user', content: '核对引用格式是否符合 GB/T 7714', ts: now - 7 * 86400000 }],
    timeline: [],
  },
] : []

export const DEMO_INTERRUPT = DEV ? {
  question: '第三章方法论初稿已生成，是否采纳？',
  options: ['采纳', '修改后采纳', '重新生成'],
} : null

/** 演示模式的「秒回」应答：与真实 SSE 的 final 事件同形态，走同一打字机管线 */
export function demoReply(text) {
  if (!DEV) return ''
  return [
    `已收到：「${String(text).slice(0, 40)}${String(text).length > 40 ? '…' : ''}」。`,
    '',
    '这是 **演示模式**（?demo=1）下的应答，不经过后端。',
    '真实环境下这里会流式返回主控智能体的编排结果与执行时间线。',
  ].join('\n')
}