import uuid
from sqlalchemy import String, Float, ForeignKey, JSON, Table, Column, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base, TimestampMixin

agent_knowledge = Table(
    "agent_knowledge",
    Base.metadata,
    Column("agent_id", Uuid, ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True),
    Column("knowledge_id", Uuid, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), primary_key=True),
)


class Agent(Base, TimestampMixin):
    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    emoji: Mapped[str] = mapped_column(String(10), default="🤖")
    style: Mapped[dict] = mapped_column(JSON, default=lambda: {"gradient": "linear-gradient(135deg, #FF6B6B, #FF8E53)"})
    description: Mapped[str] = mapped_column(String(500), default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="offline")
    system_prompt: Mapped[str] = mapped_column(String(2000), default="")
    voice_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("voices.id", ondelete="SET NULL"), nullable=True)
    speed: Mapped[float] = mapped_column(Float, default=1.0)
    volume: Mapped[float] = mapped_column(Float, default=1.0)
    pitch: Mapped[float] = mapped_column(Float, default=1.0)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, default=None, index=True)

    devices = relationship("Device", back_populates="agent", lazy="selectin")
    knowledges = relationship("KnowledgeBase", secondary=agent_knowledge, back_populates="agents", lazy="selectin")
    voice = relationship("Voice", back_populates="agents", lazy="selectin")
    user = relationship("User", lazy="selectin")
