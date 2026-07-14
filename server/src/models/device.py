import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base, TimestampMixin


class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    mac: Mapped[str] = mapped_column(String(17), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="offline")
    last_conversation: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    firmware_version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    ota_status: Mapped[str] = mapped_column(String(20), default="latest")
    auto_upgrade: Mapped[bool] = mapped_column(Boolean, default=False)
    bound_agent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    bind_code: Mapped[str | None] = mapped_column(String(6), nullable=True, default=None)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, default=None)

    agent = relationship("Agent", back_populates="devices", lazy="selectin")
    user = relationship("User", lazy="selectin")
