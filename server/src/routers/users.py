from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src import services
from src.schemas.user import NotificationUpdateRequest
from src.schemas.common import ApiResponse
import time

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/profile")
async def get_profile(db: AsyncSession = Depends(get_db)):
    data = await services.users.get_profile(db)
    return ApiResponse(data=data, timestamp=time.time())


@router.put("/notification")
async def update_notification(body: NotificationUpdateRequest):
    return ApiResponse(data=None, timestamp=time.time())
