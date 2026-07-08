from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.database import engine
from src.models.base import Base
from src.models.agent import Agent  # noqa: F401
from src.models.device import Device  # noqa: F401
from src.models.voice import Voice  # noqa: F401
from src.models.knowledge import KnowledgeBase  # noqa: F401
from src.models.conversation import Conversation, Message  # noqa: F401
from src.models.voiceprint import VoiceprintSpeaker  # noqa: F401
from src.middleware.error_handler import error_handler
from src.routers import agents, devices, voices, knowledge, conversations, voiceprints, users, pipeline
from src.ws.voice import handle_voice


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 自动执行种子数据
    from seed import seed
    await seed()
    yield
    await engine.dispose()


app = FastAPI(
    title="明境 AI 服务端",
    version="0.4.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(error_handler)

app.include_router(agents.router)
app.include_router(devices.router)
app.include_router(voices.router)
app.include_router(knowledge.router)
app.include_router(conversations.router)
app.include_router(voiceprints.router)
app.include_router(users.router)
app.include_router(pipeline.router)


@app.websocket("/ws/voice/{agent_id}")
async def ws_voice(ws: WebSocket, agent_id: str):
    await handle_voice(ws, agent_id)


@app.websocket("/ws/device/{device_id}")
async def ws_device(ws: WebSocket, device_id: str):
    from src.ws.device import handle_device
    await handle_device(ws, device_id)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
