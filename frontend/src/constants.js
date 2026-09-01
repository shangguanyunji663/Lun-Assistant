// 状态枚举标签：与后端 infrastructure/models/project.py 的 PROJECT_STATUSES 保持一致
// （单一真源在后端，由后端 Pydantic Literal 校验，前端仅做文案映射）
export const STATUS_LABEL = {
  created: '立项', topic: '选题中', literature: '文献阶段',
  writing: '写作阶段', review: '校验阶段', finalize: '已定稿',
}
