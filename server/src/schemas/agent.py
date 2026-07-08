from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.schemas.common import CamelModel


class AgentTagSchema(CamelModel):
    icon: str = ""
    label: str = ""


class AgentCreate(CamelModel):
    name: str = Field(..., min_length=1, max_length=100)
    emoji: str = "🤖"
    description: str = ""
    system_prompt: str = ""
    voice_id: UUID | None = None
    knowledge_ids: list[UUID] = Field(default_factory=list)
    device_ids: list[UUID] = Field(default_factory=list)
    tags: list[AgentTagSchema] = Field(default_factory=list)


class AgentUpdate(CamelModel):
    name: str | None = None
    emoji: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    voice_id: UUID | None = None
    knowledge_ids: list[UUID] | None = None
    device_ids: list[UUID] | None = None
    tags: list[AgentTagSchema] | None = None


class AgentResponse(CamelModel):
    id: UUID
    name: str
    emoji: str
    style: dict
    description: str
    tags: list[AgentTagSchema]
    status: str
    system_prompt: str
    voice_id: UUID | None
    knowledge_ids: list[UUID] = Field(default_factory=list)
    bound_device_ids: list[UUID] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
