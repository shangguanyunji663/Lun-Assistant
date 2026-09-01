"""认证 API 契约（请求体 + response_model）。

此前各端点直接返回裸 dict，OpenAPI 无法表达响应结构，前端无法据此生成类型；
本模块显式声明出入参，使契约可被校验、可被文档化。
"""
from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=64)


class LoginIn(BaseModel):
    username: str
    password: str


class UserBrief(BaseModel):
    id: int
    username: str
    role: str


class RegisterOut(BaseModel):
    id: int
    username: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str
    user: UserBrief
