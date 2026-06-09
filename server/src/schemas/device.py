from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.schemas.common import CamelModel


class DeviceResponse(CamelModel):
    id: UUID
    name: str
    mac: str
    status: str
    last_conversation: datetime | None
    firmware_version: str
    ota_status: str
    auto_upgrade: bool
    bound_agent_id: UUID | None
    bound_agent_name: str | None
    created_at: datetime
    updated_at: datetime


class DeviceBindRequest(CamelModel):
    code: str = Field(..., min_length=6, max_length=17)
    agent_id: UUID | None = None


class DeviceAssignRoleRequest(CamelModel):
    agent_id: UUID | None = None
