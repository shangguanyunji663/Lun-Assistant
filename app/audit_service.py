"""审计服务：全量审计日志落库（平台操作 + 工具调用共用）。"""
import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog

logger = logging.getLogger("lunjiang.audit")


async def write_audit(
    db: AsyncSession,
    *,
    user_id: int | None,
    action: str,
    resource: str = "",
    detail: dict[str, Any] | None = None,
    ip: str = "",
) -> None:
    """写入一条审计记录。审计失败不阻断业务，仅记运行日志。"""
    try:
        if detail is not None and not isinstance(detail, str):
            detail = json.loads(json.dumps(detail, ensure_ascii=False, default=str))
        db.add(AuditLog(user_id=user_id, action=action, resource=resource, detail=detail, ip=ip))
        await db.commit()
    except Exception:
        logger.exception("审计写入失败 action=%s", action)
        await db.rollback()


async def query_audit(db: AsyncSession, *, user_id: int | None = None, limit: int = 100):
    q = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
    if user_id is not None:
        q = q.where(AuditLog.user_id == user_id)
    rows = (await db.execute(q)).scalars().all()
    return [
        {
            "id": r.id, "user_id": r.user_id, "action": r.action,
            "resource": r.resource, "detail": r.detail, "ip": r.ip,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
