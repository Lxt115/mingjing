from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin


class VoiceprintSpeaker(Base, TimestampMixin):
    __tablename__ = "voiceprint_speakers"

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(200), default="")
    registered_at: Mapped[str] = mapped_column(String(20), default="")
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
