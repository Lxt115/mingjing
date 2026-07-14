import asyncio
import uuid

from sqlalchemy import select
from src.database import async_session_factory, engine
from src.models.base import Base
from src.models.agent import Agent
from src.models.device import Device               # noqa: F401
from src.models.knowledge import KnowledgeBase     # noqa: F401
from src.models.conversation import Conversation   # noqa: F401
from src.models.voice import Voice
from src.models.user import User                   # noqa: F401


SEED_VOICES = [
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000001"), "name": "温柔 · Vivi", "character": "温", "description": "中文 · 温柔自然，适合日常对话", "language": "中文", "gender": "female", "category": "female", "gradient": "linear-gradient(135deg, #f093fb, #f5576c)", "provider_voice_name": "zh_female_vv_uranus_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000002"), "name": "甜美 · Mindy", "character": "甜", "description": "中文 · 甜美活泼，适合儿童陪伴", "language": "中文", "gender": "female", "category": "female", "gradient": "linear-gradient(135deg, #4facfe, #00f2fe)", "provider_voice_name": "zh_female_xiaohe_uranus_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000003"), "name": "沉稳 · Kian", "character": "稳", "description": "中文 · 沉稳大气，适合知识讲解", "language": "中文", "gender": "male", "category": "male", "gradient": "linear-gradient(135deg, #0fd850, #f9f047)", "provider_voice_name": "zh_male_m191_uranus_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000004"), "name": "阳光 · Cedric", "character": "朗", "description": "中文 · 阳光开朗，适合儿童陪伴", "language": "中文", "gender": "male", "category": "male", "gradient": "linear-gradient(135deg, #667eea, #764ba2)", "provider_voice_name": "zh_male_taocheng_uranus_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000005"), "name": "Sweet · Dacey", "character": "En", "description": "English · Sweet & warm", "language": "英语", "gender": "female", "category": "english", "gradient": "linear-gradient(135deg, #f5af19, #f12711)", "provider_voice_name": "en_female_dacey_uranus_bigtts"},
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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        existing = (await db.execute(select(Agent))).scalars().first()
        if existing:
            print("数据已存在，跳过种子数据")
            return

        # 创建系统用户
        result = await db.execute(select(User).where(User.username == "system"))
        system_user = result.scalar_one_or_none()
        if not system_user:
            from src.services.auth import hash_password
            system_user = User(username="system", password_hash=hash_password("system"))
            db.add(system_user)
            await db.flush()

        voices = []
        for v in SEED_VOICES:
            voice = Voice(**v)
            db.add(voice)
            voices.append(voice)

        agents = []
        for i, a in enumerate(SEED_AGENTS):
            # 系统智能体不属于任何普通用户（user_id=None），新用户注册时复制
            agent = Agent(
                name=a["name"],
                emoji=a["emoji"],
                style=a["style"],
                description=a["description"],
                tags=a["tags"],
                system_prompt=a["system_prompt"],
                voice_id=voices[i % len(voices)].id,
                status="online",
                user_id=None,  # 系统预设智能体
            )
            db.add(agent)
            agents.append(agent)

        await db.commit()
        print(f"种子数据写入完成: {len(SEED_VOICES)} voices, {len(SEED_AGENTS)} agents")


if __name__ == "__main__":
    asyncio.run(seed())
