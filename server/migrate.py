"""MySQL 迁移脚本：添加 provider_voice_name 列 + 清空种子表"""
import asyncio
from sqlalchemy import text
from src.database import engine


async def migrate():
    async with engine.begin() as conn:
        # 添加新列
        try:
            # SQLite 不支持 AFTER，MySQL 支持
            await conn.execute(text(
                "ALTER TABLE voices ADD COLUMN provider_voice_name "
                "VARCHAR(100) DEFAULT ''"
            ))
            print("[OK] 列 provider_voice_name 已添加")
        except Exception as e:
            if "Duplicate column" in str(e):
                print("[SKIP] 列已存在")
            else:
                print(f"[ERROR] {e}")

        # 清空数据（让重启时 seed.py 重新写入）
        tables = [
            "agent_knowledge", "messages", "conversations",
            "devices", "agents", "voices", "voiceprint_speakers",
        ]
        for t in tables:
            await conn.execute(text(f"DELETE FROM {t}"))
            print(f"[OK] {t} 已清空")

    print("\n迁移完成，可以重启服务了")


if __name__ == "__main__":
    asyncio.run(migrate())
