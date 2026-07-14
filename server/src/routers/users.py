from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src import services
from src.models.user import User
from src.dependencies import get_current_user
from src.schemas.common import ApiResponse
import time

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/profile")
async def get_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await services.users.get_profile(db, current_user.id)
    return ApiResponse(data=data, timestamp=time.time())
