"""全量审计 HTTP 中间件：记录每个 API 请求（方法/路径/状态/耗时/用户/IP）。

- 用户身份从 Authorization 头尽力解析（不校验过期，仅用于留痕）。
- 写库以 fire-and-forget 任务执行，不阻塞响应。
"""
import time

from jwt import PyJWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

import jwt as pyjwt

from app.auth.security import decode_token
from app.db import get_session_factory
from app.audit_service import write_audit

_EXCLUDE_PATHS = {"/", "/health", "/docs", "/openapi.json", "/favicon.ico"}


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        path = request.url.path
        if path in _EXCLUDE_PATHS:
            return response

        duration_ms = int((time.perf_counter() - start) * 1000)
        user_id = None
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            try:
                user_id = int(decode_token(auth[7:])["sub"])
            except (PyJWTError, KeyError, ValueError):
                user_id = None

        session_factory = get_session_factory()
        async with session_factory() as db:
            await write_audit(
                db,
                user_id=user_id,
                action="api_request",
                resource=f"{request.method} {path}",
                detail={"status": response.status_code, "duration_ms": duration_ms},
                ip=request.client.host if request.client else "",
            )
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
        return response
