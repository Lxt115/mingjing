import uuid
from sqlalchemy import String, Integer, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base, TimestampMixin


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    title: Mapped[str] = mapped_column(String(200), nullable=False, default="新对话")
    preview: Mapped[str] = mapped_column(String(500), default="")
    agent_name: Mapped[str] = mapped_column(String(100), default="")
    agent_emoji: Mapped[str] = mapped_column(String(10), default="")
    accent_color: Mapped[str] = mapped_column(String(50), default="var(--coral)")
    accent_bg: Mapped[str] = mapped_column(String(50), default="#fff0f0")
    date_label: Mapped[str] = mapped_column(String(50), default="")
    time: Mapped[str] = mapped_column(String(10), default="")
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)

    messages = relationship("Message", back_populates="conversation", lazy="selectin", order_by="Message.created_at")


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    role: Mapped[str] = mapped_column(String(10), nullable=False)
    text: Mapped[str] = mapped_column(String(5000), nullable=False, default="")
    timestamp: Mapped[str] = mapped_column(String(30), default="")
    conversation_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("conversations.id", ondelete="CASCADE"))

    conversation = relationship("Conversation", back_populates="messages")
