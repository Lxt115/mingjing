import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.schemas.user import UserProfileResponse
from src.models.conversation import Conversation, Message
from src.models.device import Device


async def get_profile(db: AsyncSession, user_id: uuid.UUID) -> UserProfileResponse:
    # 统计对话数
    conv_result = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
    )
    total_conversations = conv_result.scalar() or 0

    # 统计绑定的设备数
    dev_result = await db.execute(
        select(func.count(Device.id)).where(Device.user_id == user_id)
    )
    bound_device_count = dev_result.scalar() or 0

    # 统计消息数，估算对话时长（每条消息约3秒）
    msg_result = await db.execute(
        select(func.count(Message.id))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == user_id)
    )
    total_messages = msg_result.scalar() or 0
    total_hours = max(1, int(total_messages * 3 / 3600))

    return UserProfileResponse(
        name="明境用户",
        user_id=str(user_id),
        version="4.0.0",
        total_conversations=total_conversations,
        total_hours=total_hours,
        bound_device_count=bound_device_count,
        avatar_emoji="👨‍👧",
    )
