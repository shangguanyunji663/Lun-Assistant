"""认证路由：注册 / 登录 / 当前用户。

认证端点接入 Redis 滑动窗口限流（复用治理层 check_rate），
按 用户名+IP 维度限制尝试频率，缓解口令爆破风险。
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.audit import write_audit
from api.auth.schemas import (
    LoginIn,
    RegisterIn,
    RegisterOut,
    TokenOut,
    UserBrief,
)
from api.auth.security import create_access_token, get_current_user, hash_password, verify_password
from infrastructure.db import get_db
from infrastructure.models.user import User
from services.governance.rate_limiter import RateLimitExceeded, check_rate

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 认证端点限流：同一 用户名+IP 每分钟 5 次
_AUTH_RPM = 5


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else ""


async def _throttle(username: str, ip: str) -> None:
    """登录/注册尝试限流；超限返回 429。Redis 故障时放行（fail-open，不锁死用户）。"""
    try:
        await check_rate(f"auth:{username}:{ip}", _AUTH_RPM)
    except RateLimitExceeded:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"尝试过于频繁，每分钟最多 {_AUTH_RPM} 次，请稍后再试")
    except Exception:
        return


@router.post("/register", response_model=RegisterOut)
async def register(body: RegisterIn, request: Request, db: AsyncSession = Depends(get_db)):
    await _throttle(body.username, _client_ip(request))
    exists = await db.scalar(select(User).where(User.username == body.username))
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "用户名已存在")
    user = User(username=body.username, password_hash=hash_password(body.password))
    db.add(user)
    await db.commit()
    await write_audit(db, user_id=user.id, action="auth", resource="register", ip=_client_ip(request))
    return RegisterOut(id=user.id, username=user.username)


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, request: Request, db: AsyncSession = Depends(get_db)):
    await _throttle(body.username, _client_ip(request))
    user = await db.scalar(select(User).where(User.username == body.username))
    if user is None or not verify_password(body.password, user.password_hash):
        await write_audit(db, user_id=None, action="auth", resource="login_failed",
                          detail={"username": body.username}, ip=_client_ip(request))
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")
    token = create_access_token(user.id, user.role)
    await write_audit(db, user_id=user.id, action="auth", resource="login", ip=_client_ip(request))
    return TokenOut(
        access_token=token,
        token_type="bearer",
        user=UserBrief(id=user.id, username=user.username, role=user.role),
    )


@router.get("/me", response_model=UserBrief)
async def me(user: User = Depends(get_current_user)):
    return UserBrief(id=user.id, username=user.username, role=user.role)
