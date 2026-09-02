"""第二层：项目结构化记忆（选题结论/大纲/研究问题等，JSON 持久化于 projects 表）。"""
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.models.project import Project

DEFAULT: dict = {
    "topic": {},        # 选题分析结论
    "outline": [],      # 论文大纲
    "facts": [],        # 关键事实/约束（字数、格式要求等）
    "progress": {},     # 各章节完成状态
}


class StructuredMemory:
    async def get(self, db: AsyncSession, project_id: int) -> dict:
        proj = await db.get(Project, project_id)
        if proj is None or not proj.structured_memory:
            return dict(DEFAULT)
        merged = dict(DEFAULT)
        merged.update(proj.structured_memory)
        return merged

    async def update(self, db: AsyncSession, project_id: int, section: str, value) -> None:
        proj = await db.get(Project, project_id)
        if proj is None:
            raise ValueError(f"项目不存在: {project_id}")
        mem = dict(proj.structured_memory or DEFAULT)
        mem[section] = value
        proj.structured_memory = mem
        await db.commit()

    def render_brief(self, mem: dict) -> str:
        """渲染为提示词用摘要文本。"""
        lines = []
        if mem.get("topic"):
            t = mem["topic"]
            lines.append(f"选题: {t.get('title', '')}（{t.get('rationale', '')}）")
        if mem.get("outline"):
            lines.append("大纲: " + " > ".join(x.get("title", "") if isinstance(x, dict) else str(x)
                                              for x in mem["outline"]))
        for f in mem.get("facts", []):
            lines.append(f"约束: {f}")
        return "\n".join(lines)


structured_memory = StructuredMemory()
