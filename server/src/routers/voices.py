import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.voice import Voice
from src.providers.factory import get_tts
from src import services
from src.schemas.common import ApiResponse
import time

router = APIRouter(prefix="/api/voices", tags=["voices"])


@router.get("")
async def list_voices(db: AsyncSession = Depends(get_db)):
    data = await services.voices.list_voices(db)
    return ApiResponse(data=data, timestamp=time.time())


@router.put("/{voice_id}/select")
async def select_voice(voice_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    ok = await services.voices.select_voice(db, voice_id)
    if not ok:
        raise HTTPException(status_code=404, detail="声音不存在")
    return ApiResponse(data=None, timestamp=time.time())


@router.post("/clone", status_code=201)
async def clone_voice():
    raise HTTPException(status_code=501, detail="Voice cloning not yet implemented")


@router.get("/{voice_id}/preview")
async def preview_voice(voice_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """试听音色 —— 用该音色合成一段短文本并返回 MP3"""
    result = await db.execute(select(Voice).where(Voice.id == voice_id))
    voice = result.scalar_one_or_none()
    if not voice:
        raise HTTPException(status_code=404, detail="声音不存在")

    provider_name = voice.provider_voice_name or ""
    tts = get_tts()
    try:
        audio = await tts.synthesize(
            text="你好，欢迎使用语音合成服务，这是我的声音。",
            voice_name=provider_name,
        )
        return Response(content=audio, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"试听失败: {e}")
