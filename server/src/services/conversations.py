import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.conversation import Conversation, Message
from src.schemas.conversation import ConversationListResponse, ConversationResponse, MessageResponse


async def list_conversations(db: AsyncSession, user_id: uuid.UUID, filter_str: str | None = None) -> list[ConversationListResponse]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
    )
    conversations = result.scalars().all()
    items = [_to_list_item(c) for c in conversations]
    if filter_str and filter_str != "全部":
        items = [i for i in items if i.agent_name == filter_str or i.date_label == filter_str]
    return items


async def get_conversation(db: AsyncSession, conv_id: uuid.UUID, user_id: uuid.UUID) -> ConversationResponse | None:
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conv_id, Conversation.user_id == user_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        return None
    return _to_detail_response(conv)


async def get_messages(db: AsyncSession, conv_id: uuid.UUID, user_id: uuid.UUID) -> list[MessageResponse] | None:
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conv_id, Conversation.user_id == user_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        return None
    return [_message_to_response(m) for m in (conv.messages or [])]


def _to_list_item(c: Conversation) -> ConversationListResponse:
    return ConversationListResponse(
        id=c.id,
        title=c.title,
        preview=c.preview,
        agent_name=c.agent_name,
        agent_emoji=c.agent_emoji,
        accent_color=c.accent_color,
        date_label=c.date_label,
        time=c.time,
        message_count=c.message_count,
        agent_id=str(c.agent_id) if c.agent_id else None,
    )


def _to_detail_response(c: Conversation) -> ConversationResponse:
    return ConversationResponse(
        id=c.id,
        title=c.title,
        meta=f"{c.agent_name} · {c.date_label} {c.time} · {c.message_count} 条消息",
        agent_name=c.agent_name,
        agent_emoji=c.agent_emoji,
        accent_color=c.accent_color,
        accent_bg=c.accent_bg,
        messages=[_message_to_response(m) for m in (c.messages or [])],
    )


def _message_to_response(m: Message) -> MessageResponse:
    return MessageResponse(
        id=m.id,
        role=m.role,
        text=m.text,
        timestamp=m.timestamp,
    )
