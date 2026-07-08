from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base, TimestampMixin


class Voice(Base, TimestampMixin):
    __tablename__ = "voices"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    character: Mapped[str] = mapped_column(String(100), default="")
    description: Mapped[str] = mapped_column(String(500), default="")
    language: Mapped[str] = mapped_column("voice_lang", String(50), default="zh-CN")
    gender: Mapped[str] = mapped_column(String(20), default="female")
    is_cloned: Mapped[bool] = mapped_column(default=False)
    is_selected: Mapped[bool] = mapped_column(default=False)
    gradient: Mapped[str] = mapped_column(String(200), default="linear-gradient(135deg, #FF6B6B, #FF8E53)")
    category: Mapped[str] = mapped_column(String(50), default="female")
    # 实际的 TTS 提供商音色名（如 longanhuan、zh-CN-XiaoxiaoNeural）
    provider_voice_name: Mapped[str] = mapped_column(String(100), default="")

    agents = relationship("Agent", back_populates="voice", lazy="selectin")
