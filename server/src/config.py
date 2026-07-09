import asyncio
import sys

import dashscope
from pydantic_settings import BaseSettings

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class Settings(BaseSettings):
    # ── 数据库（默认 MySQL）──
    db_type: str = "mysql"           # mysql | sqlite
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = "123456"
    db_name: str = "mingjing"
    # 直接指定 URL 可覆盖以上所有（兼容旧配置）
    database_url: str = ""

    @property
    def db_url(self) -> str:
        """返回 SQLAlchemy async 连接字符串"""
        if self.database_url:
            return self.database_url
        if self.db_type == "sqlite":
            return f"sqlite+aiosqlite:///./{self.db_name}.db"
        return f"mysql+aiomysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"

    # ── Provider 选择 ──
    # stt:  bailian  | openai
    stt_provider: str = "bailian"
    # tts:  bailian  | edge
    tts_provider: str = "bailian"
    # llm:  bailian  | openai | deepseek
    llm_provider: str = "deepseek"

    # ── API Keys ──
    dashscope_api_key: str = ""
    openai_api_key: str = ""
    openai_base_url: str = ""      # 自定义端点，DeepSeek 填 https://api.deepseek.com/v1
    deepseek_api_key: str = ""     # DeepSeek API key（也可复用 openai_api_key）

    # ── LLM 模型名 ──
    openai_model: str = "gpt-4o-mini"
    deepseek_model: str = "deepseek-chat"  # V4-Flash，不开思考模式

    # ── TTS 音色 ──
    edge_tts_voice: str = "zh-CN-XiaoxiaoNeural"

    # ── 联网搜索 ──
    # 搜索服务商：metaso | tavily
    search_provider: str = "metaso"
    search_api_key: str = ""
    search_max_results: int = 3

    # ── 服务 ──
    server_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

dashscope.api_key = settings.dashscope_api_key
