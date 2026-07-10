import uuid
import re
import base64
import asyncio
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import settings
from src.models.agent import Agent
from src.models.conversation import Conversation, Message
from src.providers.factory import get_stt, get_llm, get_tts
from src.services.rag import build_knowledge_context
from src.services.memory import build_memory_injection, summarize_and_save
from src.services.prompt_manager import get_prompt_manager, EMOJI_MAP
from src.services.plugins import build_tools_prompt, extract_tool_calls, remove_tool_tags, execute_tool
from src.services.tts_utils import clean_tts_text

CHINA_TZ = timezone(timedelta(hours=8))
MAX_HISTORY_MESSAGES = 20

# 预编译正则，避免每次 _handle_tool_calls 都重新编译
SEARCH_TAG_CLEAN_RE = re.compile(r"<SEARCH>.*?</SEARCH>", re.DOTALL)


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
            conv.time = datetime.now(CHINA_TZ).strftime("%H:%M")
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
            time=datetime.now(CHINA_TZ).strftime("%H:%M"),
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
    client_ip: str = "",
) -> tuple[str, list[dict]]:
    history = await _load_history(db, conversation_id) if conversation_id else []

    knowledge_prompt = ""
    if agent.knowledges:
        knowledge_ids = [k.id for k in agent.knowledges if k.is_enabled]
        if knowledge_ids:
            knowledge_prompt = await build_knowledge_context(db, knowledge_ids, user_text)

    # ── 使用 PromptManager 构建增强系统提示词（时间/日期/农历/位置/天气）──
    pm = get_prompt_manager()
    system_prompt = pm.build_enhanced_prompt(
        base_prompt=agent.system_prompt or "",
        agent_id=str(agent.id),
        location=settings.weather_default_location,
        client_ip=client_ip,
        language="中文",
        emoji_enabled=True,
    )

    # ── 注入记忆到 <memory> 标签 ──
    memory_text = build_memory_injection(agent.id)
    if memory_text and "<memory>" in system_prompt:
        system_prompt = re.sub(
            r"<memory>.*?</memory>",
            f"<memory>\n{memory_text}\n</memory>",
            system_prompt,
            flags=re.DOTALL,
        )

    if knowledge_prompt:
        system_prompt = system_prompt + "\n\n" + knowledge_prompt

    # ── 注入可用工具列表 ──
    tools_prompt = build_tools_prompt()
    if tools_prompt:
        system_prompt = system_prompt + "\n\n" + tools_prompt

    messages = history + [{"role": "user", "content": user_text}]

    return system_prompt, messages


async def _synthesize_audio(agent: Agent, text: str) -> tuple[bytes, str]:
    voice_name = _pick_voice_name(agent)
    tts = get_tts()
    audio_bytes = b""
    audio_error = ""
    try:
        clean_text = clean_tts_text(text)
        audio_bytes = await tts.synthesize(
            text=clean_text,
            voice_name=voice_name,
            speed=agent.speed,
            volume=agent.volume,
            pitch=agent.pitch,
        )
    except Exception as e:
        audio_error = str(e)
        print(f"[TTS] 合成失败: {audio_error}")
    return audio_bytes, audio_error


async def chat_pipeline(
    db: AsyncSession,
    text: str,
    agent_id: uuid.UUID,
    conversation_id: uuid.UUID | None = None,
    client_ip: str = "",
) -> dict:
    agent = await _load_agent(db, agent_id)
    if not agent:
        return {"error": "角色不存在"}

    system_prompt, messages = await _build_llm_messages(db, agent, text, conversation_id, client_ip)

    llm = get_llm()
    llm_text = await llm.chat(messages=messages, system_prompt=system_prompt)

    audio_bytes, audio_error = await _synthesize_audio(agent, llm_text)

    conv_id = await _persist_conversation(db, conversation_id, agent, text, llm_text)

    # ── 异步保存记忆（不阻塞响应）──
    asyncio.create_task(_save_memory_bg(agent.id, text, llm_text))

    emoji, emotion = _extract_emoji(llm_text)

    return {
        "text": llm_text,
        "emoji": emoji,
        "emotion": emotion,
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
    client_ip: str = "",
) -> dict:
    stt = get_stt()
    text = await stt.transcribe(audio_bytes, audio_format)
    if text.startswith("["):
        return {"error": text}

    result = await chat_pipeline(db, text, agent_id, conversation_id, client_ip)
    result["transcribed_text"] = text
    return result


async def speech_pipeline_stream(
    db: AsyncSession,
    audio_bytes: bytes,
    audio_format: str,
    agent_id: uuid.UUID,
    conversation_id: uuid.UUID | None = None,
    client_ip: str = "",
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

    system_prompt, messages = await _build_llm_messages(db, agent, text, conversation_id, client_ip)

    llm = get_llm()

    full_text = ""
    search_depth = 0
    tool_depth = 0

    while True:
        round_text = ""
        async for token in llm.chat_stream(messages=messages, system_prompt=system_prompt):
            if token.startswith("["):
                yield {"type": "error", "message": token}
                return
            round_text += token

        messages, full_text, search_depth, tool_depth, should_continue = await _handle_tool_calls(
            round_text, messages, full_text, search_depth, tool_depth,
        )
        if not should_continue:
            break

    # 发送文本流
    final_answer = full_text
    yield {"type": "text_chunk", "content": final_answer}

    print(f"[PIPELINE] LLM done, answer_len={len(final_answer)}, starting TTS...")
    voice_name = _pick_voice_name(agent)
    print(f"[PIPELINE] voice_name={voice_name}")
    tts = get_tts()
    print(f"[PIPELINE] tts provider type={type(tts).__name__}")
    audio_error = ""
    total_tts_bytes = 0
    total_tts_chunks = 0
    print(f"[TTS] 音色: {voice_name}, 文本长度: {len(final_answer)}")
    try:
        tts_text = clean_tts_text(final_answer)
        async for chunk in tts.synthesize_streaming(
            text=tts_text,
            voice_name=voice_name,
            speed=agent.speed,
            volume=agent.volume,
            pitch=agent.pitch,
        ):
            total_tts_bytes += len(chunk)
            total_tts_chunks += 1
            yield {"type": "audio_chunk", "content": base64.b64encode(chunk).decode()}
        print(f"[DEBUG] TTS stream: {total_tts_chunks} chunks, {total_tts_bytes} bytes, ~{total_tts_bytes//32}ms")
    except Exception as e:
        audio_error = str(e)
        print(f"[TTS] 流式合成失败: {audio_error}")

    conv_id = await _persist_conversation(db, conversation_id, agent, text, final_answer)

    # ── 异步保存记忆（不阻塞响应）──
    asyncio.create_task(_save_memory_bg(agent.id, text, final_answer))

    emoji, emotion = _extract_emoji(final_answer)

    yield {
        "type": "audio_done",
        "audio_format": "pcm",
        "audio_error": audio_error,
        "conversation_id": str(conv_id),
        "emoji": emoji,
        "emotion": emotion,
    }
    yield {"type": "done"}


async def chat_pipeline_stream(
    db: AsyncSession,
    text: str,
    agent_id: uuid.UUID,
    conversation_id: uuid.UUID | None = None,
    client_ip: str = "",
):
    agent = await _load_agent(db, agent_id)
    if not agent:
        yield {"type": "error", "message": "角色不存在"}
        return

    system_prompt, messages = await _build_llm_messages(db, agent, text, conversation_id, client_ip)

    llm = get_llm()

    full_text = ""
    search_depth = 0
    tool_depth = 0

    while True:
        round_text = ""
        async for token in llm.chat_stream(messages=messages, system_prompt=system_prompt):
            if token.startswith("["):
                yield {"type": "error", "message": token}
                return
            round_text += token

        messages, full_text, search_depth, tool_depth, should_continue = await _handle_tool_calls(
            round_text, messages, full_text, search_depth, tool_depth,
        )
        if not should_continue:
            break

    final_answer = full_text
    yield {"type": "text_chunk", "content": final_answer}

    voice_name = _pick_voice_name(agent)
    tts = get_tts()
    audio_error = ""
    try:
        tts_text = clean_tts_text(final_answer)
        async for chunk in tts.synthesize_streaming(
            text=tts_text,
            voice_name=voice_name,
            speed=agent.speed,
            volume=agent.volume,
            pitch=agent.pitch,
        ):
            yield {"type": "audio_chunk", "content": base64.b64encode(chunk).decode()}
    except Exception as e:
        audio_error = str(e)
        print(f"[TTS] chat流式合成失败: {audio_error}")

    conv_id = await _persist_conversation(db, conversation_id, agent, text, final_answer)

    # ── 异步保存记忆（不阻塞响应）──
    asyncio.create_task(_save_memory_bg(agent.id, text, final_answer))

    emoji, emotion = _extract_emoji(final_answer)

    yield {
        "type": "audio_done",
        "audio_format": "pcm",
        "audio_error": audio_error,
        "conversation_id": str(conv_id),
        "emoji": emoji,
        "emotion": emotion,
    }
    yield {"type": "done"}


async def _save_memory_bg(agent_id: uuid.UUID, user_text: str, ai_text: str) -> None:
    """后台异步保存记忆（不阻塞主流程）。"""
    try:
        llm = get_llm()
        messages = [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": ai_text},
        ]
        await summarize_and_save(agent_id, messages, llm)
    except Exception as e:
        print(f"[memory] 后台记忆保存失败: {e}")


async def _handle_tool_calls(text: str, messages: list[dict], full_text: str, 
                       search_depth: int, tool_depth: int) -> tuple[list[dict], str, int, int, bool]:
    """检测并处理文本中的搜索和工具调用标签。
    
    Returns: (messages, full_text, search_depth, tool_depth, should_continue)
    """
    MAX_SEARCH_DEPTH = 3
    MAX_TOOL_DEPTH = 3

    # 先处理工具调用
    tool_calls = extract_tool_calls(text)
    if tool_calls and tool_depth < MAX_TOOL_DEPTH:
        tool_depth += 1
        clean_text = remove_tool_tags(text)
        if clean_text:
            full_text += clean_text
        for tool_name, params in tool_calls:
            print(f"[DEBUG] 工具调用 #{tool_depth}: {tool_name}({params[:50]})")
            result = await execute_tool(tool_name, params)
            if result:
                messages.append({
                    "role": "user",
                    "content": f"【工具执行结果：{tool_name}】\n{result.result}\n\n请基于以上结果继续回答用户。",
                })
        return messages, full_text, search_depth, tool_depth, True

    # 再处理联网搜索
    from src.services.web_search import extract_search_query, search
    search_query = extract_search_query(text)
    if search_query and search_depth < MAX_SEARCH_DEPTH:
        search_depth += 1
        print(f"[DEBUG] 联网搜索 #{search_depth}: {search_query}")
        search_result = search(search_query)
        clean_text = SEARCH_TAG_CLEAN_RE.sub("", text).strip()
        if clean_text:
            full_text += clean_text
        messages.append({
            "role": "user",
            "content": f"【联网搜索结果】\n{search_result}\n\n请基于以上搜索结果回答用户的问题。如果搜索结果不足以回答，可以再次搜索。",
        })
        return messages, full_text, search_depth, tool_depth, True

    # 无需工具或搜索，去除标签后返回
    clean_text = remove_tool_tags(text)
    clean_text = SEARCH_TAG_CLEAN_RE.sub("", clean_text) if search_depth > 0 or tool_depth > 0 else text
    full_text += clean_text
    return messages, full_text, search_depth, tool_depth, False


def _extract_emoji(text: str) -> tuple[str, str]:
    """从 LLM 输出首字符提取 emoji 情绪。返回 (emoji, emotion)。"""
    if text and text[0] in EMOJI_MAP:
        emoji = text[0]
        emotion = EMOJI_MAP[emoji]
        return emoji, emotion
    return "", "neutral"


def _pick_voice_name(agent: Agent) -> str:
    """根据 Agent 关联的 Voice 获取实际 TTS 音色名。

    优先级：
    1. agent.voice.provider_voice_name — Voice 模型的映射字段
    2. agent.voice.name — 作为后备
    3. 性别二选一 — 最终兜底
    """
    if agent.voice:
        if agent.voice.provider_voice_name:
            return agent.voice.provider_voice_name
        # 如果没有 provider_voice_name，尝试用 name 作为音色名
        return agent.voice.name
    # 无关联 Voice，默认 female 音色
    return "longanhuan"


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
