import asyncio
import sys

import dashscope
from pydantic_settings import BaseSettings

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./mingjing_dev.db"

    dashscope_api_key: str = ""

    server_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

dashscope.api_key = settings.dashscope_api_key
