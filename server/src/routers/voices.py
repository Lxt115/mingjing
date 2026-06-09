import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
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
async def clone_voice(db: AsyncSession = Depends(get_db)):
    return ApiResponse(data={"id": str(uuid.uuid4()), "name": "我的声音克隆", "isCloned": True}, timestamp=time.time())
