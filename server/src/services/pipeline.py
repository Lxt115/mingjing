import uuid
import base64

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.agent import Agent
from src.models.voice import Voice
from src.models.conversation import Conversation, Message
from src.providers.factory import get_stt, get_llm, get_tts
from src.services.rag import build_knowledge_context
from datetime import datetime, timezone

MAX_HISTORY_MESSAGES = 20


async def _load_agent(db: AsyncSession, agent_id: uuid.UUID) -> Agent | None:
    result = await db.execute(
        select(Agent)
        .options(selectinload(Agent.voice), selectinload(Agent.knowledges))
        .where(Agent.id == agent_id)
    )
    return result.scalar_one_or_none()


async def _load_history(db: AsyncSession, conversation_id: uuid.UUID) -> list[dict]:
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv or not conv.messages:
        return []

    msgs = sorted(conv.messages, key=lambda m: m.created_at)
    recent = msgs[-MAX_HISTORY_MESSAGES:]

    role_map = {"ai": "assistant", "user": "user", "system": "system"}
    return [{"role": role_map.get(m.role, m.role), "content": m.text} for m in recent]


async def _persist_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID | None,
    agent: Agent,
    user_text: str,
    llm_text: str,
) -> uuid.UUID:
    if conversation_id:
        conv_result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = conv_result.scalar_one_or_none()
        if conv:
            conv.preview = user_text[:50]
            conv.time = datetime.now().strftime("%H:%M")
            conv.message_count = conv.message_count + 2
            await db.flush()
        else:
            conversation_id = None

    if not conversation_id:
        conv = Conversation(
            title=_make_title(user_text),
            preview=user_text[:50],
            agent_name=agent.name,
            agent_emoji=agent.emoji,
            agent_id=agent.id,
            accent_color=_agent_color(agent),
            accent_bg=_agent_bg(agent),
            date_label="今天",
            time=datetime.now().strftime("%H:%M"),
            message_count=2,
        )
        db.add(conv)
        await db.flush()

    now_str = datetime.now(timezone.utc).isoformat()
    db.add(Message(role="user", text=user_text, timestamp=now_str, conversation_id=conv.id))
    db.add(Message(role="ai", text=llm_text, timestamp=now_str, conversation_id=conv.id))
    await db.commit()
    return conv.id


async def _build_llm_messages(
    db: AsyncSession,
    agent: Agent,
    user_text: str,
    conversation_id: uuid.UUID | None,
) -> tuple[str, list[dict]]:
    history = await _load_history(db, conversation_id) if conversation_id else []

    knowledge_prompt = ""
    if agent.knowledges:
        knowledge_ids = [k.id for k in agent.knowledges if k.is_enabled]
        if knowledge_ids:
            knowledge_prompt = await build_knowledge_context(db, knowledge_ids, user_text)

    system_prompt = agent.system_prompt or ""
    if knowledge_prompt:
        if system_prompt:
            system_prompt = system_prompt + "\n\n" + knowledge_prompt
        else:
            system_prompt = knowledge_prompt

    messages = history + [{"role": "user", "content": user_text}]

    return system_prompt, messages


async def _synthesize_audio(agent: Agent, text: str) -> tuple[bytes, str]:
    voice_name = _pick_voice_name(agent)
    tts = get_tts()
    audio_bytes = b""
    audio_error = ""
    try:
        audio_bytes = await tts.synthesize(
            text=text,
            voice_name=voice_name,
            speed=agent.speed,
            volume=agent.volume,
            pitch=agent.pitch,
        )
    except Exception as e:
        audio_error = str(e)
    return audio_bytes, audio_error


async def chat_pipeline(
    db: AsyncSession,
    text: str,
    agent_id: uuid.UUID,
    conversation_id: uuid.UUID | None = None,
) -> dict:
    agent = await _load_agent(db, agent_id)
    if not agent:
        return {"error": "角色不存在"}

    system_prompt, messages = await _build_llm_messages(db, agent, text, conversation_id)

    llm = get_llm()
    llm_text = await llm.chat(messages=messages, system_prompt=system_prompt)

    audio_bytes, audio_error = await _synthesize_audio(agent, llm_text)

    conv_id = await _persist_conversation(db, conversation_id, agent, text, llm_text)

    return {
        "text": llm_text,
        "audio": base64.b64encode(audio_bytes).decode(),
        "audio_format": "mp3",
        "audio_error": audio_error,
        "conversation_id": str(conv_id),
    }


async def speech_pipeline(
    db: AsyncSession,
    audio_bytes: bytes,
    audio_format: str,
    agent_id: uuid.UUID,
    conversation_id: uuid.UUID | None = None,
) -> dict:
    stt = get_stt()
    text = await stt.transcribe(audio_bytes, audio_format)
    if text.startswith("["):
        return {"error": text}

    result = await chat_pipeline(db, text, agent_id, conversation_id)
    result["transcribed_text"] = text
    return result


async def speech_pipeline_stream(
    db: AsyncSession,
    audio_bytes: bytes,
    audio_format: str,
    agent_id: uuid.UUID,
    conversation_id: uuid.UUID | None = None,
):
    stt = get_stt()
    text = await stt.transcribe(audio_bytes, audio_format)
    if text.startswith("["):
        yield {"type": "error", "message": text}
        return

    yield {"type": "transcript", "content": text}

    agent = await _load_agent(db, agent_id)
    if not agent:
        yield {"type": "error", "message": "角色不存在"}
        return

    system_prompt, messages = await _build_llm_messages(db, agent, text, conversation_id)

    llm = get_llm()
    full_text = ""
    async for token in llm.chat_stream(
        messages=messages,
        system_prompt=system_prompt,
    ):
        if token.startswith("["):
            yield {"type": "error", "message": token}
            return
        full_text += token
        yield {"type": "text_chunk", "content": token}

    voice_name = _pick_voice_name(agent)
    tts = get_tts()
    audio_error = ""
    total_tts_bytes = 0
    total_tts_chunks = 0
    try:
        async for chunk in tts.synthesize_streaming(
            text=full_text,
            voice_name=voice_name,
            speed=agent.speed,
            volume=agent.volume,
            pitch=agent.pitch,
        ):
            total_tts_bytes += len(chunk)
            total_tts_chunks += 1
            yield {"type": "audio_chunk", "content": base64.b64encode(chunk).decode()}
        print(f"[DEBUG] TTS stream: {total_tts_chunks} chunks, {total_tts_bytes} bytes, ~{total_tts_bytes//44}ms")
    except Exception as e:
        audio_error = str(e)

    conv_id = await _persist_conversation(db, conversation_id, agent, text, full_text)

    yield {
        "type": "audio_done",
        "audio_format": "pcm",
        "audio_error": audio_error,
        "conversation_id": str(conv_id),
    }
    yield {"type": "done"}


async def chat_pipeline_stream(
    db: AsyncSession,
    text: str,
    agent_id: uuid.UUID,
    conversation_id: uuid.UUID | None = None,
):
    agent = await _load_agent(db, agent_id)
    if not agent:
        yield {"type": "error", "message": "角色不存在"}
        return

    system_prompt, messages = await _build_llm_messages(db, agent, text, conversation_id)

    llm = get_llm()
    full_text = ""
    async for token in llm.chat_stream(
        messages=messages,
        system_prompt=system_prompt,
    ):
        if token.startswith("["):
            yield {"type": "error", "message": token}
            return
        full_text += token
        yield {"type": "text_chunk", "content": token}

    voice_name = _pick_voice_name(agent)
    tts = get_tts()
    audio_error = ""
    try:
        async for chunk in tts.synthesize_streaming(
            text=full_text,
            voice_name=voice_name,
            speed=agent.speed,
            volume=agent.volume,
            pitch=agent.pitch,
        ):
            yield {"type": "audio_chunk", "content": base64.b64encode(chunk).decode()}
    except Exception as e:
        audio_error = str(e)

    conv_id = await _persist_conversation(db, conversation_id, agent, text, full_text)

    yield {
        "type": "audio_done",
        "audio_format": "pcm",
        "audio_error": audio_error,
        "conversation_id": str(conv_id),
    }
    yield {"type": "done"}


def _pick_voice_name(agent: Agent) -> str:
    is_male = agent.voice and agent.voice.gender == "male"
    return "longanyang" if is_male else "longanhuan"


def _make_title(text: str) -> str:
    t = text.strip()
    if len(t) <= 15:
        return t
    return t[:14] + "…"


def _agent_color(agent: Agent) -> str:
    style = agent.style or {}
    g = style.get("gradient", "")
    if "#FF6B6B" in g or "coral" in g.lower():
        return "var(--coral)"
    if "#5C6BC0" in g or "indigo" in g.lower():
        return "var(--indigo)"
    if "#00C9A7" in g or "teal" in g.lower():
        return "var(--teal)"
    if "#FFB830" in g or "amber" in g.lower():
        return "var(--amber)"
    return "var(--coral)"


def _agent_bg(agent: Agent) -> str:
    style = agent.style or {}
    g = style.get("gradient", "")
    if "#FF6B6B" in g or "coral" in g.lower():
        return "#fff0f0"
    if "#5C6BC0" in g or "indigo" in g.lower():
        return "#eef0fc"
    if "#00C9A7" in g or "teal" in g.lower():
        return "#e8fdf5"
    if "#FFB830" in g or "amber" in g.lower():
        return "#fff8e6"
    return "#fff0f0"
