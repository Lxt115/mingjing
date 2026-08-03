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
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000001"), "name": "天才童声", "character": "灵", "description": "中文 · 机灵童声，适合儿童陪伴", "language": "中文", "gender": "male", "category": "male", "gradient": "linear-gradient(135deg, #f093fb, #f5576c)", "provider_voice_name": "zh_male_tiancaitongsheng_uranus_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000002"), "name": "佩琪", "character": "萌", "description": "中文 · 俏皮女童声", "language": "中文", "gender": "female", "category": "female", "gradient": "linear-gradient(135deg, #4facfe, #00f2fe)", "provider_voice_name": "zh_female_peiqi_uranus_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000003"), "name": "樱桃丸子", "character": "甜", "description": "中文 · 甜美可爱，适合日常陪伴", "language": "中文", "gender": "female", "category": "female", "gradient": "linear-gradient(135deg, #ff9a9e, #fecfef)", "provider_voice_name": "zh_female_yingtaowanzi_mars_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000004"), "name": "鲁班七号", "character": "酷", "description": "中文 · 活力少年音", "language": "中文", "gender": "male", "category": "male", "gradient": "linear-gradient(135deg, #0fd850, #f9f047)", "provider_voice_name": "zh_male_lubanqihao_uranus_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000005"), "name": "林间女孩", "character": "清", "description": "中文 · 清新自然女声", "language": "中文", "gender": "female", "category": "female", "gradient": "linear-gradient(135deg, #43e97b, #38f9d7)", "provider_voice_name": "zh_female_linjianvhai_moon_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000006"), "name": "呆萌川妹", "character": "萌", "description": "中文 · 呆萌可爱，带四川味", "language": "中文", "gender": "female", "category": "female", "gradient": "linear-gradient(135deg, #f6d365, #fda085)", "provider_voice_name": "zh_female_daimengchuanmei_moon_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000007"), "name": "熊二", "character": "憨", "description": "中文 · 憨厚卡通男声", "language": "中文", "gender": "male", "category": "male", "gradient": "linear-gradient(135deg, #a8edea, #fed6e3)", "provider_voice_name": "zh_male_xionger_mars_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000008"), "name": "美托洁儿", "character": "柔", "description": "中文 · 温柔治愈女声", "language": "中文", "gender": "female", "category": "female", "gradient": "linear-gradient(135deg, #c471f5, #fa71cd)", "provider_voice_name": "zh_female_meituojieer_moon_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000009"), "name": "开朗弟弟", "character": "朗", "description": "中文 · 阳光男孩童声", "language": "中文", "gender": "male", "category": "male", "gradient": "linear-gradient(135deg, #30cfd0, #330867)", "provider_voice_name": "zh_male_kailangdidi_uranus_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-00000000000a"), "name": "Sophie", "character": "暖", "description": "中文 · 温柔成熟女声", "language": "中文", "gender": "female", "category": "female", "gradient": "linear-gradient(135deg, #fc466b, #3f5efb)", "provider_voice_name": "zh_female_sophie_uranus_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-00000000000b"), "name": "婆婆", "character": "慈", "description": "中文 · 慈祥和蔼婆婆音", "language": "中文", "gender": "female", "category": "female", "gradient": "linear-gradient(135deg, #a1c4fd, #c2e9fb)", "provider_voice_name": "zh_female_popo_mars_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-00000000000c"), "name": "弯弯小河", "character": "纯", "description": "中文 · 清澈甜美少女音", "language": "中文", "gender": "female", "category": "female", "gradient": "linear-gradient(135deg, #00c6ff, #0072ff)", "provider_voice_name": "zh_female_wanwanxiaohe_moon_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-00000000000d"), "name": "周杰伦 · emo", "character": "飒", "description": "中文 · 周杰伦风格男声", "language": "中文", "gender": "male", "category": "male", "gradient": "linear-gradient(135deg, #7f00ff, #e100ff)", "provider_voice_name": "zh_male_zhoujielun_emo_v2_mars_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-00000000000e"), "name": "广西圆舟", "character": "趣", "description": "中文 · 圆润少年音", "language": "中文", "gender": "male", "category": "male", "gradient": "linear-gradient(135deg, #11998e, #38ef7d)", "provider_voice_name": "zh_male_guangxiyuanzhou_moon_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-00000000000f"), "name": "月雨女", "character": "婉", "description": "中文 · 婉约女声", "language": "中文", "gender": "female", "category": "female", "gradient": "linear-gradient(135deg, #667eea, #764ba2)", "provider_voice_name": "zh_female_yueyunv_mars_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000010"), "name": "北京小爷", "character": "痞", "description": "中文 · 京腔痞帅男声", "language": "中文", "gender": "male", "category": "male", "gradient": "linear-gradient(135deg, #f83600, #f9d423)", "provider_voice_name": "zh_male_beijingxiaoye_moon_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000011"), "name": "万曲大叔", "character": "豪", "description": "中文 · 浑厚大叔音", "language": "中文", "gender": "female", "category": "female", "gradient": "linear-gradient(135deg, #5f2c82, #49a09d)", "provider_voice_name": "zh_female_wanqudashu_moon_bigtts"},
    {"id": uuid.UUID("a1000000-0000-0000-0000-000000000012"), "name": "宇宙自选", "character": "奇", "description": "中文 · 神秘科幻感男声", "language": "中文", "gender": "male", "category": "male", "gradient": "linear-gradient(135deg, #0f0c29, #302b63)", "provider_voice_name": "zh_male_yuzhouzixuan_moon_bigtts"},
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
