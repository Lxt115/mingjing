from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base, TimestampMixin


class KnowledgeBase(Base, TimestampMixin):
    __tablename__ = "knowledge_bases"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    item_count: Mapped[int] = mapped_column(default=0)
    item_unit: Mapped[str] = mapped_column(String(50), default="条")
    status: Mapped[str] = mapped_column(String(20), default="enabled")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content: Mapped[list] = mapped_column(JSON, default=list)

    agents = relationship("Agent", secondary="agent_knowledge", back_populates="knowledges", lazy="selectin")
