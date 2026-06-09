import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.knowledge import KnowledgeBase

MAX_RAG_CHUNKS = 5
CHUNK_SEPARATORS = re.compile(r"[。！？.!?\n]+")


def _split_into_chunks(text: str, max_chunk_len: int = 500) -> list[str]:
    parts = CHUNK_SEPARATORS.split(text)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if current_len + len(part) > max_chunk_len and current:
            chunks.append("。".join(current) + "。")
            current = []
            current_len = 0
        current.append(part)
        current_len += len(part)
    if current:
        chunks.append("。".join(current) + "。")
    return chunks


def _keyword_score(chunk: str, query: str) -> float:
    query_chars = set(query)
    chunk_lower = chunk.lower()
    query_lower = query.lower()
    score = 0.0
    for qc in query_chars:
        if qc in chunk_lower:
            score += 1.0
    if query_lower in chunk_lower:
        score += 5.0
    query_terms = query_lower.split()
    for term in query_terms:
        if len(term) >= 2 and term in chunk_lower:
            score += 3.0
    return score


async def retrieve_relevant_knowledge(
    db: AsyncSession,
    knowledge_ids: list,
    query: str,
    max_chunks: int = MAX_RAG_CHUNKS,
) -> str:
    if not knowledge_ids:
        return ""

    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id.in_(knowledge_ids),
            KnowledgeBase.is_enabled == True,
        )
    )
    knowledge_bases = result.scalars().all()

    if not knowledge_bases:
        return ""

    all_chunks: list[tuple[str, float]] = []
    for kb in knowledge_bases:
        content_items = kb.content or []
        for item in content_items:
            if isinstance(item, str):
                chunks = _split_into_chunks(item)
                for chunk in chunks:
                    if chunk:
                        score = _keyword_score(chunk, query)
                        all_chunks.append((chunk, score))

    if not all_chunks:
        return ""

    all_chunks.sort(key=lambda x: x[1], reverse=True)
    top_chunks = all_chunks[:max_chunks]

    top_chunks = [c for c, s in top_chunks if c and s >= 0]
    if not top_chunks:
        top_chunks = [c for c, _ in all_chunks[:max_chunks]]

    sections = []
    for i, chunk in enumerate(top_chunks):
        sections.append(f"[{i + 1}] {chunk}")

    return "\n\n".join(sections)


async def build_knowledge_context(
    db: AsyncSession,
    knowledge_ids: list,
    query: str,
) -> str:
    knowledge_text = await retrieve_relevant_knowledge(db, knowledge_ids, query)
    if not knowledge_text:
        return ""

    return (
        "你可以参考以下知识库中的内容来回答用户问题。如果参考了知识库内容，请自然地融入回答中，"
        "不要使用\"根据知识库\"、\"参考资料显示\"等表述：\n\n" + knowledge_text
    )
