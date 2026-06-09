from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.user import UserProfileResponse


async def get_profile(db: AsyncSession) -> UserProfileResponse:
    return UserProfileResponse(
        name="明境用户",
        user_id="MJ-20240405",
        version="4.0.0",
        total_conversations=127,
        total_hours=43,
        bound_device_count=2,
        avatar_emoji="👨‍👧",
    )
