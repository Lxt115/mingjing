import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.voiceprint import VoiceprintSpeaker
from src.schemas.voiceprint import VoiceprintSpeakerResponse


async def list_speakers(db: AsyncSession) -> list[VoiceprintSpeakerResponse]:
    result = await db.execute(select(VoiceprintSpeaker).order_by(VoiceprintSpeaker.created_at.desc()))
    speakers = result.scalars().all()
    return [_to_response(s) for s in speakers]


async def register_speaker(db: AsyncSession, name: str) -> VoiceprintSpeakerResponse:
    speaker = VoiceprintSpeaker(
        name=name,
        registered_at=datetime.now().strftime("%Y-%m-%d"),
        sample_count=1,
    )
    db.add(speaker)
    await db.commit()
    await db.refresh(speaker)
    return _to_response(speaker)


async def delete_speaker(db: AsyncSession, speaker_id: uuid.UUID) -> bool:
    result = await db.execute(select(VoiceprintSpeaker).where(VoiceprintSpeaker.id == speaker_id))
    speaker = result.scalar_one_or_none()
    if not speaker:
        return False
    await db.delete(speaker)
    await db.commit()
    return True


def _to_response(s: VoiceprintSpeaker) -> VoiceprintSpeakerResponse:
    return VoiceprintSpeakerResponse(
        id=s.id,
        name=s.name,
        registered_at=s.registered_at,
        sample_count=s.sample_count,
    )
