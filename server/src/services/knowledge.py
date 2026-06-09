import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.knowledge import KnowledgeBase
from src.schemas.knowledge import KnowledgeResponse


async def list_knowledge_bases(db: AsyncSession) -> list[KnowledgeResponse]:
    result = await db.execute(select(KnowledgeBase).order_by(KnowledgeBase.is_system.desc(), KnowledgeBase.created_at))
    kbs = result.scalars().all()
    return [_to_response(k) for k in kbs]


async def get_knowledge_content(db: AsyncSession, kb_id: uuid.UUID) -> list[str]:
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        return []
    return kb.content or []


async def toggle_knowledge(db: AsyncSession, kb_id: uuid.UUID, enabled: bool) -> bool:
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        return False
    kb.is_enabled = enabled
    kb.status = "enabled" if enabled else "disabled"
    await db.commit()
    return True


async def toggle_memory(db: AsyncSession, enabled: bool) -> bool:
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.is_system == True).limit(1)
    )
    kb = result.scalar_one_or_none()
    if not kb:
        kb = KnowledgeBase(
            name="记忆库",
            description="自动保存的对话摘要和知识点",
            item_count=0,
            item_unit="条",
            status="enabled" if enabled else "disabled",
            is_system=True,
            is_enabled=enabled,
            last_updated=datetime.now(timezone.utc),
        )
        db.add(kb)
        await db.commit()
        await db.refresh(kb)
    else:
        kb.is_enabled = enabled
        kb.status = "enabled" if enabled else "disabled"
        kb.last_updated = datetime.now(timezone.utc)
        await db.commit()
    return True


async def upload_knowledge(db: AsyncSession, name: str, content_text: str = "") -> KnowledgeResponse:
    content_list = [content_text] if content_text.strip() else []

    kb = KnowledgeBase(
        name=name,
        description="1 个文件" if content_text else "空知识库",
        item_count=1 if content_text else 0,
        item_unit="个文件",
        status="enabled",
        is_system=False,
        is_enabled=True,
        last_updated=datetime.now(timezone.utc),
        content=content_list,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return _to_response(kb)


async def add_content_to_knowledge(db: AsyncSession, kb_id: uuid.UUID, texts: list[str]) -> bool:
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        return False

    existing = kb.content or []
    existing.extend(texts)
    kb.content = existing
    kb.item_count = len(existing)
    kb.last_updated = datetime.now(timezone.utc)
    await db.commit()
    return True


async def delete_knowledge(db: AsyncSession, kb_id: uuid.UUID) -> bool:
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        return False
    await db.delete(kb)
    await db.commit()
    return True


async def get_knowledge_detail(db: AsyncSession, kb_id: uuid.UUID) -> dict | None:
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        return None
    return {
        **_to_response(kb).model_dump(by_alias=True),
        "content": kb.content or [],
    }


async def delete_content(db: AsyncSession, kb_id: uuid.UUID, index: int) -> bool:
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        return False
    content = kb.content or []
    if index < 0 or index >= len(content):
        return False
    content.pop(index)
    kb.content = content
    kb.item_count = len(content)
    kb.description = f"{len(content)} 个文件" if len(content) else "空知识库"
    kb.last_updated = datetime.now(timezone.utc)
    await db.commit()
    return True


def _to_response(kb: KnowledgeBase) -> KnowledgeResponse:
    return KnowledgeResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        item_count=kb.item_count,
        item_unit=kb.item_unit,
        status=kb.status,
        is_system=kb.is_system,
        is_enabled=kb.is_enabled,
        last_updated=kb.last_updated,
    )
