from datetime import datetime
from uuid import UUID

from src.schemas.common import CamelModel


class KnowledgeResponse(CamelModel):
    id: UUID
    name: str
    description: str
    item_count: int
    item_unit: str
    status: str
    is_system: bool
    is_enabled: bool
    last_updated: datetime | None


class KnowledgeDetailResponse(KnowledgeResponse):
    content: list[str] = []


class KnowledgeToggleRequest(CamelModel):
    enabled: bool


class KnowledgeContentRequest(CamelModel):
    texts: list[str]
