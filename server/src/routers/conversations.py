import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src import services
from src.models.user import User
from src.dependencies import get_current_user
from src.schemas.common import ApiResponse
import time

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
async def list_conversations(
    filter: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await services.conversations.list_conversations(db, current_user.id, filter)
    return ApiResponse(data=data, timestamp=time.time())


@router.get("/{conv_id}")
async def get_conversation(
    conv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = await services.conversations.get_conversation(db, conv_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    return ApiResponse(data=conv, timestamp=time.time())


@router.get("/{conv_id}/messages")
async def get_messages(
    conv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    messages = await services.conversations.get_messages(db, conv_id, current_user.id)
    if messages is None:
        raise HTTPException(status_code=404, detail="对话不存在")
    return ApiResponse(data=messages, timestamp=time.time())
