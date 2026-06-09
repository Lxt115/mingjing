import json
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.ws.manager import manager
from src.database import async_session_factory
from src.models.device import Device
from src.services import pipeline


async def handle_device(ws: WebSocket, device_id: str):
    import uuid as uuid_mod
    try:
        device_uuid = uuid_mod.UUID(device_id)
    except ValueError:
        await ws.close(code=1008, reason="invalid device_id")
        return

    async with async_session_factory() as db:
        result = await db.execute(
            select(Device).options(selectinload(Device.agent)).where(Device.id == device_uuid)
        )
        device = result.scalar_one_or_none()
        if not device:
            await ws.close(code=1008, reason="device not found")
            return

        agent_id = device.bound_agent_id

        device.status = "online"
        await db.commit()

    if not agent_id:
        await ws.close(code=1008, reason="no agent bound")
        return

    conn = await manager.connect(ws, agent_id, device_uuid)
    await manager.send_json(ws, {
        "type": "welcome",
        "device_id": str(device_uuid),
        "agent_id": str(agent_id),
        "mac": device.mac,
        "firmware_version": device.firmware_version,
    })

    try:
        async for raw in ws.iter_text():
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type", "")

            if msg_type == "button_press":
                conn.audio_chunks = []
                conn.is_recording = True
                await manager.send_json(ws, {"type": "status", "message": "listening"})

            elif msg_type == "audio_chunk":
                if conn.is_recording:
                    data = msg.get("data", "")
                    if data:
                        import base64
                        try:
                            conn.audio_chunks.append(base64.b64decode(data))
                        except Exception:
                            pass

            elif msg_type == "button_release":
                if not conn.is_recording:
                    continue
                conn.is_recording = False

                if not conn.audio_chunks:
                    await manager.send_json(ws, {"type": "status", "message": "no_audio"})
                    continue

                audio_bytes = b"".join(conn.audio_chunks)
                conn.audio_chunks = []

                await manager.send_json(ws, {"type": "status", "message": "processing"})

                async with async_session_factory() as db2:
                    try:
                        async for event in pipeline.speech_pipeline_stream(
                            db2, audio_bytes, "pcm", agent_id, conn.conversation_id,
                        ):
                            event_type = event["type"]

                            if event_type == "transcript":
                                await manager.send_json(ws, {
                                    "type": "transcript",
                                    "text": event["content"],
                                })

                            elif event_type == "text_chunk":
                                await manager.send_json(ws, {
                                    "type": "text_chunk",
                                    "content": event["content"],
                                })

                            elif event_type == "error":
                                await manager.send_json(ws, {
                                    "type": "error",
                                    "message": event["message"],
                                })
                                return

                            elif event_type == "audio":
                                conn.conversation_id = uuid_mod.UUID(event["conversation_id"])
                                await manager.send_json(ws, {
                                    "type": "response",
                                    "text": "",
                                    "audio": event["audio"],
                                    "audio_format": event["audio_format"],
                                    "audio_error": event.get("audio_error", ""),
                                    "conversation_id": event["conversation_id"],
                                })

                            elif event_type == "done":
                                pass

                    except Exception as e:
                        await manager.send_json(ws, {"type": "error", "message": str(e)})

            elif msg_type == "status":
                await manager.send_json(ws, {
                    "type": "status_ack",
                    "battery": msg.get("battery", -1),
                    "wifi_rssi": msg.get("wifi_rssi", -1),
                })

            elif msg_type == "ping":
                await manager.send_json(ws, {"type": "pong"})

    except WebSocketDisconnect:
        pass
    finally:
        async with async_session_factory() as db3:
            result = await db3.execute(select(Device).where(Device.id == device_uuid))
            dev = result.scalar_one_or_none()
            if dev:
                dev.status = "offline"
                await db3.commit()
        manager.disconnect(ws)
