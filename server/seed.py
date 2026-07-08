import asyncio
import uuid

from sqlalchemy import select
from src.database import async_session_factory
from src.models.agent import Agent
from src.models.voice import Voice


SEED_VOICES = [
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000001"), "name": "甜美 · 活泼", "character": "甜", "description": "中文 · 适合儿童陪伴", "language": "中文", "gender": "female", "category": "female", "gradient": "linear-gradient(135deg, #f093fb, #f5576c)", "provider_voice_name": "longanhuan"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000002"), "name": "温柔 · 安心", "character": "温", "description": "中文 · 适合睡前故事", "language": "中文", "gender": "female", "category": "female", "gradient": "linear-gradient(135deg, #4facfe, #00f2fe)", "provider_voice_name": "zh-CN-XiaoxiaoNeural"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000003"), "name": "朗朗 · 阳光", "character": "朗", "description": "中文 · 适合儿童陪伴", "language": "中文", "gender": "male", "category": "male", "gradient": "linear-gradient(135deg, #0fd850, #f9f047)", "provider_voice_name": "longanyang"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000004"), "name": "沉稳 · 知识感", "character": "稳", "description": "中文 · 适合科普问答", "language": "中文", "gender": "male", "category": "male", "gradient": "linear-gradient(135deg, #4facfe, #00f2fe)", "provider_voice_name": "zh-CN-YunxiNeural"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000005"), "name": "Lily · 美式英语", "character": "En", "description": "English · 亲切自然", "language": "英语", "gender": "female", "category": "english", "gradient": "linear-gradient(135deg, #667eea, #764ba2)", "provider_voice_name": "en-US-JennyNeural"},
]

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
                status="online",
            )
            db.add(agent)
            agents.append(agent)

        await db.commit()
        print(f"种子数据写入完成: {len(SEED_VOICES)} voices, {len(SEED_AGENTS)} agents")


if __name__ == "__main__":
    asyncio.run(seed())
