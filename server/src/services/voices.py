from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.voice import Voice
from src.schemas.voice import VoiceResponse


async def list_voices(db: AsyncSession) -> list[VoiceResponse]:
    result = await db.execute(select(Voice).order_by(Voice.category, Voice.created_at))
    voices = result.scalars().all()
    return [_to_response(v) for v in voices]


async def select_voice(db: AsyncSession, voice_id) -> bool:
    result = await db.execute(select(Voice))
    voices = result.scalars().all()
    found = False
    for v in voices:
        v.is_selected = (v.id == voice_id)
        if v.id == voice_id:
            found = True
    if found:
        await db.commit()
    return found


def _to_response(v: Voice) -> VoiceResponse:
    return VoiceResponse(
        id=v.id,
        name=v.name,
        character=v.character,
        description=v.description,
        language=v.language,
        gender=v.gender,
        is_cloned=v.is_cloned,
        is_selected=v.is_selected,
        gradient=v.gradient,
        category=v.category,
        provider_voice_name=v.provider_voice_name or "",
    )
