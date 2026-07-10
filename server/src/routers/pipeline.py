import uuid
import base64
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import Field

from src.database import get_db
from src import services
from src.schemas.common import ApiResponse, CamelModel
from src.schemas.pipeline import ChatPipelineResponse
import time

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class ChatRequest(CamelModel):
    text: str = Field(..., min_length=1)
    agent_id: uuid.UUID
    conversation_id: uuid.UUID | None = None


class SpeechRequest(CamelModel):
    audio: str = Field(..., description="base64 audio")
    audio_format: str = "webm"
    agent_id: uuid.UUID
    conversation_id: uuid.UUID | None = None


@router.post("/chat")
async def chat(body: ChatRequest, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.headers.get("x-real-ip") or request.client.host if request.client else ""
    result = await services.pipeline.chat_pipeline(db, body.text, body.agent_id, body.conversation_id, client_ip=client_ip)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return ApiResponse(data=ChatPipelineResponse(**result).model_dump(by_alias=True), timestamp=time.time())


@router.post("/speech")
async def speech(body: SpeechRequest, request: Request, db: AsyncSession = Depends(get_db)):
    raw = body.audio
    if "," in raw:
        raw = raw.split(",")[1]
    audio_bytes = base64.b64decode(raw)

    client_ip = request.headers.get("x-real-ip") or request.client.host if request.client else ""
    result = await services.pipeline.speech_pipeline(db, audio_bytes, body.audio_format, body.agent_id, body.conversation_id, client_ip=client_ip)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return ApiResponse(data=ChatPipelineResponse(**result).model_dump(by_alias=True), timestamp=time.time())
