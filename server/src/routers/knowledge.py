import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src import services
from src.schemas.knowledge import KnowledgeToggleRequest, KnowledgeContentRequest
from src.schemas.common import ApiResponse
import time

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("")
async def list_knowledge(db: AsyncSession = Depends(get_db)):
    data = await services.knowledge.list_knowledge_bases(db)
    return ApiResponse(data=data, timestamp=time.time())


@router.put("/memory/toggle")
async def toggle_memory(body: KnowledgeToggleRequest, db: AsyncSession = Depends(get_db)):
    await services.knowledge.toggle_memory(db, body.enabled)
    return ApiResponse(data=None, timestamp=time.time())


@router.post("/upload", status_code=201)
async def upload_knowledge(file: UploadFile = File(...), name: str = Form(""), db: AsyncSession = Depends(get_db)):
    display_name = name or file.filename or "未命名"
    content_text = ""
    try:
        raw = await file.read()
        try:
            content_text = raw.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content_text = raw.decode("gbk")
            except UnicodeDecodeError:
                content_text = raw.decode("utf-8", errors="replace")
    except Exception:
        pass
    kb = await services.knowledge.upload_knowledge(db, display_name, content_text)
    return ApiResponse(data=kb, timestamp=time.time())


@router.get("/{kb_id}")
async def get_knowledge_detail(kb_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    kb = await services.knowledge.get_knowledge_detail(db, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return ApiResponse(data=kb, timestamp=time.time())


@router.put("/{kb_id}/toggle")
async def toggle_knowledge(kb_id: uuid.UUID, body: KnowledgeToggleRequest, db: AsyncSession = Depends(get_db)):
    ok = await services.knowledge.toggle_knowledge(db, kb_id, body.enabled)
    if not ok:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return ApiResponse(data=None, timestamp=time.time())


@router.post("/{kb_id}/add", status_code=201)
async def add_knowledge_content(kb_id: uuid.UUID, body: KnowledgeContentRequest, db: AsyncSession = Depends(get_db)):
    ok = await services.knowledge.add_content_to_knowledge(db, kb_id, body.texts)
    if not ok:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return ApiResponse(data=None, timestamp=time.time())


@router.delete("/{kb_id}")
async def delete_knowledge(kb_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    ok = await services.knowledge.delete_knowledge(db, kb_id)
    if not ok:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return ApiResponse(data=None, timestamp=time.time())


@router.delete("/{kb_id}/content/{index}")
async def delete_content(kb_id: uuid.UUID, index: int, db: AsyncSession = Depends(get_db)):
    ok = await services.knowledge.delete_content(db, kb_id, index)
    if not ok:
        raise HTTPException(status_code=404, detail="知识库或内容不存在")
    return ApiResponse(data=None, timestamp=time.time())
