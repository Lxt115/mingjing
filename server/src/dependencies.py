from fastapi import Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.user import User
from src.services.auth import decode_access_token


async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="未登录，请先登录")
    # 支持 "Bearer xxx" 和直接传 token 两种格式
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user
