"""审计服务：全量审计日志落库（平台操作 + 工具调用共用）。

合规硬约束（见 project_memory）：审计参数超 200 字符必须截断，
仅存哈希指纹 + 摘要，避免整段正文（论文全文/长文本入参）进入日志。
净化在唯一落库口 write_audit 统一完成，覆盖 HTTP/认证/工具三条入口。
"""
import hashlib
import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.config import get_value
from infrastructure.models.audit import AuditLog

logger = logging.getLogger("lunjiang.audit")

_DEFAULT_SANITIZE_CHARS = 200


def _sanitize_value(value: Any, chars: int) -> Any:
    """递归净化 detail：字符串超限 → {指纹, 摘要, 长度}，其余类型原样保留。

    - 指纹: sha256 前 16 位，供人工审计对账（相同原文指纹可复现）；
    - 摘要: 保留前 chars 字符（默认 200），兼顾可读性与可用信息量；
    - 长度: 记录原文长度，便于统计超限字段占比。
    """
    if isinstance(value, dict):
        return {k: _sanitize_value(v, chars) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_value(v, chars) for v in value]
    if isinstance(value, str) and len(value) > chars:
        return {
            "fp": hashlib.sha256(value.encode("utf-8")).hexdigest()[:16],
            "sum": value[:chars],
            "len": len(value),
        }
    return value


def sanitize_detail(detail: dict[str, Any] | None, chars: int | None = None) -> dict[str, Any] | None:
    """审计 detail 统一净化入口（纯函数，便于单测）。"""
    if detail is None:
        return None
    chars = chars or int(get_value("governance", "audit", "sanitize_chars",
                                   default=_DEFAULT_SANITIZE_CHARS))
    out = _sanitize_value(detail, chars)
    return out if isinstance(out, dict) else {"value": out}


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
            detail = sanitize_detail(detail)   # 合规：超限参数截断 + 哈希指纹 + 摘要
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
