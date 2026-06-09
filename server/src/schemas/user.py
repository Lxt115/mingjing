from src.schemas.common import CamelModel


class UserProfileResponse(CamelModel):
    name: str
    user_id: str
    version: str
    total_conversations: int
    total_hours: int
    bound_device_count: int
    avatar_emoji: str


class NotificationUpdateRequest(CamelModel):
    enabled: bool
