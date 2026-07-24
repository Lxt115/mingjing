import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src import services
from src.schemas.voiceprint import VoiceprintRegisterRequest
from src.schemas.common import ApiResponse
import time

router = APIRouter(prefix="/api/voiceprint", tags=["voiceprint"])


@router.get("")
async def list_speakers(db: AsyncSession = Depends(get_db)):
    data = await services.voiceprints.list_speakers(db)
    return ApiResponse(data=data, timestamp=time.time())


@router.post("/register", status_code=201)
async def register_speaker(body: VoiceprintRegisterRequest, db: AsyncSession = Depends(get_db)):
    speaker = await services.voiceprints.register_speaker(db, body.name, body.description)
    return ApiResponse(data=speaker, timestamp=time.time())


@router.delete("/{speaker_id}")
async def delete_speaker(speaker_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    ok = await services.voiceprints.delete_speaker(db, speaker_id)
    if not ok:
        raise HTTPException(status_code=404, detail="说话人不存在")
    return ApiResponse(data=None, timestamp=time.time())
