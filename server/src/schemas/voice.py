from uuid import UUID

from src.schemas.common import CamelModel


class VoiceResponse(CamelModel):
    id: UUID
    name: str
    character: str
    description: str
    language: str
    gender: str
    is_cloned: bool
    is_selected: bool
    gradient: str
    category: str
