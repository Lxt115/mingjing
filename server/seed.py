import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from src.database import async_session_factory
from src.models.agent import Agent
from src.models.device import Device
from src.models.voice import Voice
from src.models.knowledge import KnowledgeBase
from src.models.conversation import Conversation, Message
from src.models.voiceprint import VoiceprintSpeaker


SEED_VOICES = [
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000001"), "name": "甜美 · 活泼", "character": "甜", "description": "中文 · 适合儿童陪伴", "language": "中文", "gender": "female", "category": "female", "gradient": "linear-gradient(135deg, #f093fb, #f5576c)"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000002"), "name": "温柔 · 安心", "character": "温", "description": "中文 · 适合睡前故事", "language": "中文", "gender": "female", "category": "female", "gradient": "linear-gradient(135deg, #4facfe, #00f2fe)"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000003"), "name": "朗朗 · 阳光", "character": "朗", "description": "中文 · 适合儿童陪伴", "language": "中文", "gender": "male", "category": "male", "gradient": "linear-gradient(135deg, #0fd850, #f9f047)"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000004"), "name": "沉稳 · 知识感", "character": "稳", "description": "中文 · 适合科普问答", "language": "中文", "gender": "male", "category": "male", "gradient": "linear-gradient(135deg, #4facfe, #00f2fe)"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000005"), "name": "Lily · 美式英语", "character": "En", "description": "English · 亲切自然", "language": "英语", "gender": "female", "category": "english", "gradient": "linear-gradient(135deg, #667eea, #764ba2)"},
]

SEED_KNOWLEDGE: list = []

SEED_AGENTS = [
    {
        "name": "笃笃",
        "emoji": "🌟",
        "style": {"gradient": "linear-gradient(135deg, var(--coral), #FF8E53)"},
        "description": "活泼可爱的学习小伙伴，专注数学和英语启蒙，适合6-12岁小朋友",
        "tags": [{"icon": "🧮", "label": "数学"}, {"icon": "🌍", "label": "英语"}, {"icon": "📖", "label": "故事"}],
        "system_prompt": "你是明境AI陪伴机器人的默认伙伴，名叫笃笃，是一个活泼可爱的学习小伙伴。专注于帮助6-12岁的小朋友学习数学和英语。",
    },
    {
        "name": "故事大王",
        "emoji": "🦉",
        "style": {"gradient": "linear-gradient(135deg, #a78bfa, #7c3aed)"},
        "description": "睡前故事专家，用温柔声音陪伴入眠，包含经典童话与自创故事",
        "tags": [{"icon": "🌙", "label": "睡前故事"}, {"icon": "🐾", "label": "动物世界"}],
        "system_prompt": "你是一个温柔的故事大王，擅长讲述各种童话故事和睡前故事。语调温和，充满想象力。",
    },
    {
        "name": "数学思维",
        "emoji": "🧮",
        "style": {"gradient": "linear-gradient(135deg, var(--teal), #6EECD6)"},
        "description": "培养逻辑思维与数学兴趣",
        "tags": [{"icon": "🧠", "label": "数学"}, {"icon": "🎯", "label": "逻辑"}],
        "system_prompt": "你是数学思维导师，善于引导小朋友发现数学的乐趣。",
    },
]

SEED_DEVICES = [
    {"name": "设备 101", "mac": "44:1b:**:**:06:90", "firmware_version": "2.0.5", "ota_status": "pending"},
    {"name": "设备 102", "mac": "44:1b:**:**:07:12", "firmware_version": "2.0.5", "ota_status": "latest", "status": "offline"},
]

SEED_SPEAKERS = [
    {"id": uuid.UUID("d4000000-0000-0000-0000-000000000001"), "name": "小婷", "registered_at": "2026-04-01", "sample_count": 3},
    {"id": uuid.UUID("d4000000-0000-0000-0000-000000000002"), "name": "小明", "registered_at": "2026-04-02", "sample_count": 2},
]

SEED_CONVERSATIONS = [
    {
        "id": uuid.UUID("c3000000-0000-0000-0000-000000000001"),
        "title": "数学思维 · 苹果题",
        "preview": "小明有12个苹果，给了小红3个…",
        "agent_name": "笃笃", "agent_emoji": "🧮",
        "accent_color": "var(--teal)", "accent_bg": "#e8fdf5",
        "date_label": "今天", "time": "14:23",
        "messages": [
            {"role": "user", "text": "笃笃，小明有12个苹果，给了小红3个，还剩几个？"},
            {"role": "ai", "text": "嗨！这是个减法问题哦！\n小明原来有 12 个苹果，给了小红 3 个，所以：\n12 - 3 = 9 个\n小明还剩 9 个苹果！🍎 你答对了吗？"},
            {"role": "user", "text": "对的！那如果再给小华5个呢？"},
            {"role": "ai", "text": "很棒！继续算！\n小明还有 9 个苹果，再给小华 5 个：\n9 - 5 = 4 个\n小明最后还有 4 个苹果 🍎🍎🍎🍎！你是数学小达人！"},
        ],
    },
    {
        "id": uuid.UUID("c3000000-0000-0000-0000-000000000002"),
        "title": "英语启蒙 · 动物单词",
        "preview": "Cat的发音是/kæt/…",
        "agent_name": "笃笃", "agent_emoji": "🌍",
        "accent_color": "var(--indigo)", "accent_bg": "#eef0fc",
        "date_label": "今天", "time": "10:19",
        "messages": [
            {"role": "user", "text": "笃笃，猫用英语怎么说？"},
            {"role": "ai", "text": "Cat！发音是 /kæt/，听起来像\u201c卡特\u201d。Cat 这个单词很简单，记住了吗？🐱"},
            {"role": "user", "text": "那狗呢？"},
            {"role": "ai", "text": "Dog！发音是 /dɒɡ/，听起来像\u201c道格\u201d。Cat 和 Dog 是英语里最常见的动物单词，你已经会两个了！🐶"},
        ],
    },
    {
        "id": uuid.UUID("c3000000-0000-0000-0000-000000000003"),
        "title": "睡前故事 · 小熊和森林",
        "preview": "从前，在一片大森林里住着…",
        "agent_name": "故事大王", "agent_emoji": "📖",
        "accent_color": "var(--coral)", "accent_bg": "#fff0f0",
        "date_label": "昨天", "time": "20:05",
        "messages": [
            {"role": "user", "text": "给我讲一个小熊的故事吧"},
            {"role": "ai", "text": "从前，在一片大森林里住着一只叫豆豆的小熊。豆豆有一双大眼睛，棕色的毛发软软的，最爱吃蜂蜜🍯"},
            {"role": "user", "text": "后来发生什么了？"},
            {"role": "ai", "text": "有一天，豆豆在森林里散步，发现了一棵神奇的大树，树上有一个金色的蜂巢，里面传来甜甜的香气…要继续听吗？"},
        ],
    },
]


async def seed():
    async with async_session_factory() as db:
        existing = (await db.execute(select(Agent))).scalars().first()
        if existing:
            print("数据已存在，跳过种子数据")
            return

        voices = []
        for v in SEED_VOICES:
            voice = Voice(**v)
            db.add(voice)
            voices.append(voice)

        kbs = []
        for k in SEED_KNOWLEDGE:
            kb = KnowledgeBase(**k)
            db.add(kb)
            kbs.append(kb)

        agents = []
        for i, a in enumerate(SEED_AGENTS):
            agent = Agent(
                name=a["name"],
                emoji=a["emoji"],
                style=a["style"],
                description=a["description"],
                tags=a["tags"],
                system_prompt=a["system_prompt"],
                voice_id=voices[i % len(voices)].id,
                status="online" if i < 2 else "offline",
            )
            db.add(agent)
            agents.append(agent)

        for i, d in enumerate(SEED_DEVICES):
            device = Device(
                name=d["name"],
                mac=d["mac"],
                firmware_version=d["firmware_version"],
                ota_status=d["ota_status"],
                status=d.get("status", "online"),
                bound_agent_id=agents[i % len(agents)].id if i < len(agents) else None,
            )
            db.add(device)

        for s in SEED_SPEAKERS:
            db.add(VoiceprintSpeaker(**s))

        now_str = datetime.now(timezone.utc).isoformat()
        for c in SEED_CONVERSATIONS:
            conv = Conversation(
                id=c["id"],
                title=c["title"],
                preview=c["preview"],
                agent_name=c["agent_name"],
                agent_emoji=c["agent_emoji"],
                accent_color=c["accent_color"],
                accent_bg=c["accent_bg"],
                date_label=c["date_label"],
                time=c["time"],
                message_count=len(c["messages"]),
            )
            db.add(conv)
            for msg_data in c["messages"]:
                msg = Message(
                    role=msg_data["role"],
                    text=msg_data["text"],
                    timestamp=now_str,
                    conversation_id=c["id"],
                )
                db.add(msg)

        await db.commit()
        print(f"种子数据写入完成: {len(SEED_VOICES)} voices, {len(SEED_KNOWLEDGE)} kbs, {len(SEED_AGENTS)} agents, {len(SEED_DEVICES)} devices, {len(SEED_SPEAKERS)} speakers, {len(SEED_CONVERSATIONS)} conversations")


if __name__ == "__main__":
    asyncio.run(seed())
