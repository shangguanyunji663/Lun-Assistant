"""JWT 认证与密码散列（原 Java 安全模块的 Python 化）。"""
import time
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.config import get_value
from infrastructure.db import get_db
from infrastructure.models.user import User

_ALGO = "HS256"
_EXPIRE_SECONDS = 24 * 3600
_bearer = HTTPBearer(auto_error=False)


def _secret() -> str:
    return get_value("app", "secret_key")


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:
        return False


def create_access_token(user_id: int, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + _EXPIRE_SECONDS,
    }
    return jwt.encode(payload, _secret(), algorithm=_ALGO)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, _secret(), algorithms=[_ALGO])


async def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI 依赖：从 Bearer Token 解析当前用户。"""
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "未提供认证凭证")
    try:
        payload = decode_token(cred.credentials)
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Token 无效: {e}") from e
    user = await db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户不存在或已禁用")
    return user


def require_role(*roles: str):
    """依赖工厂：要求当前用户角色在指定集合内。"""
    async def _dep(user: User = Depends(get_current_user)) -> User:
        if roles and user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"需要角色: {roles}")
        return user
    return _dep
