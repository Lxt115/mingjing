from uuid import UUID

from src.schemas.common import CamelModel


class MessageResponse(CamelModel):
    id: UUID
    role: str
    text: str
    timestamp: str


class ConversationListResponse(CamelModel):
    id: UUID
    title: str
    preview: str
    agent_name: str
    agent_emoji: str
    accent_color: str
    date_label: str
    time: str
    message_count: int
    agent_id: str | None = None


class ConversationResponse(CamelModel):
    id: UUID
    title: str
    meta: str
    agent_name: str
    agent_emoji: str
    accent_color: str
    accent_bg: str
    messages: list[MessageResponse]
