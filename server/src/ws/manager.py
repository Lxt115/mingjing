import uuid
import base64
import asyncio
from dataclasses import dataclass, field
from fastapi import WebSocket


@dataclass
class Connection:
    websocket: WebSocket
    agent_id: uuid.UUID
    device_id: uuid.UUID | None = None
    audio_chunks: list[bytes] = field(default_factory=list)
    is_recording: bool = False
    conversation_id: uuid.UUID | None = None


class ConnectionManager:
    def __init__(self):
        self._connections: dict[WebSocket, Connection] = {}
        self._device_map: dict[str, Connection] = {}

    async def connect(self, ws: WebSocket, agent_id: uuid.UUID, device_id: uuid.UUID | None = None) -> Connection:
        await ws.accept()
        conn = Connection(websocket=ws, agent_id=agent_id, device_id=device_id)
        self._connections[ws] = conn
        if device_id:
            self._device_map[str(device_id)] = conn
        return conn

    def disconnect(self, ws: WebSocket):
        conn = self._connections.pop(ws, None)
        if conn and conn.device_id:
            self._device_map.pop(str(conn.device_id), None)

    def get(self, ws: WebSocket) -> Connection | None:
        return self._connections.get(ws)

    def get_by_device(self, device_id: str) -> Connection | None:
        return self._device_map.get(device_id)

    async def send_json(self, ws: WebSocket, data: dict):
        import json
        try:
            await ws.send_text(json.dumps(data, ensure_ascii=False))
        except Exception:
            self.disconnect(ws)

    async def broadcast_status(self, message: str):
        for ws in list(self._connections.keys()):
            await self.send_json(ws, {"type": "status", "message": message})

    @property
    def active_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()
