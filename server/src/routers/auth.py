from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src import services
from src.models.user import User
from src.dependencies import get_current_user
from src.schemas.common import ApiResponse
import time

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class LoginRequest(BaseModel):
    username: str = Field(...)
    password: str = Field(...)


class AuthResponse(BaseModel):
    token: str
    user_id: str


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await services.auth.register_user(db, body.username, body.password)
    if not user:
        raise HTTPException(status_code=409, detail="用户名已存在")
    # 新用户注册后，自动复制系统预设智能体
    count = await services.agents.copy_system_agents_for_user(db, user.id)
    print(f"[auth] 用户 {body.username} 注册成功，复制了 {count} 个智能体")
    token = services.auth.create_access_token(user.id)
    return ApiResponse(data=AuthResponse(token=token, user_id=str(user.id)), timestamp=time.time())


@router.post("/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await services.auth.authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = services.auth.create_access_token(user.id)
    return ApiResponse(data=AuthResponse(token=token, user_id=str(user.id)), timestamp=time.time())


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return ApiResponse(data={
        "user_id": str(current_user.id),
        "username": current_user.username,
    }, timestamp=time.time())
