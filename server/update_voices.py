"""一次性脚本：将数据库音色库替换为最新的 18 个系统音色（幂等，可重复执行）。

服务器执行方式（后端容器内）:
    docker compose exec backend python update_voices.py
"""
import asyncio

from src.database import async_session_factory
from src.models.voice import Voice
from seed import SEED_VOICES


async def main():
    updated, inserted = 0, 0
    async with async_session_factory() as db:
        for v in SEED_VOICES:
            existing = await db.get(Voice, v["id"])
            if existing:
                for k, val in v.items():
                    setattr(existing, k, val)
                updated += 1
            else:
                db.add(Voice(**v))
                inserted += 1
        await db.commit()
        print(f"音色同步完成: 更新 {updated} 条, 新增 {inserted} 条")


if __name__ == "__main__":
    asyncio.run(main())
