import uuid
from src.schemas.common import CamelModel


class ChatPipelineResponse(CamelModel):
    text: str
    audio: str = ""
    audio_format: str = "mp3"
    audio_error: str = ""
    conversation_id: uuid.UUID | None = None
    transcribed_text: str | None = None
