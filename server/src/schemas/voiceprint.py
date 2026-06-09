from uuid import UUID

from pydantic import Field

from src.schemas.common import CamelModel


class VoiceprintSpeakerResponse(CamelModel):
    id: UUID
    name: str
    registered_at: str
    sample_count: int


class VoiceprintRegisterRequest(CamelModel):
    name: str = Field(..., min_length=1, max_length=50)
    voice_sample_id: str = ""
