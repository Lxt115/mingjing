import json
import base64
from fastapi import WebSocket, WebSocketDisconnect

from src.ws.manager import manager
from src.database import async_session_factory
from src.services import pipeline


async def handle_voice(ws: WebSocket, agent_id: str):
    import uuid as uuid_mod
    try:
        agent_uuid = uuid_mod.UUID(agent_id)
    except ValueError:
        await ws.close(code=1008, reason="invalid agent_id")
        return

    conn = await manager.connect(ws, agent_uuid)
    await manager.send_json(ws, {"type": "welcome", "agent_id": str(agent_uuid)})

    try:
        async for raw in ws.iter_text():
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type", "")

            if msg_type == "audio_start":
                conn.is_recording = True
                conn.audio_chunks.clear()
                await manager.send_json(ws, {"type": "status", "message": "recording"})

            elif msg_type == "audio_chunk":
                raw_data = msg.get("data", "")
                if raw_data and conn.is_recording:
                    conn.audio_chunks.append(raw_data)
                    if not hasattr(conn, '_chunk_count'):
                        conn._chunk_count = 0
                    conn._chunk_count += 1

            elif msg_type == "audio_end":
                chunk_count = getattr(conn, '_chunk_count', 0)
                print(f"[DEBUG] audio_end: received {chunk_count} chunks")
                conn._chunk_count = 0
                conn.is_recording = False
                if not conn.audio_chunks:
                    await manager.send_json(ws, {"type": "status", "message": "no audio"})
                    continue

                audio_bytes = b"".join(base64.b64decode(c) for c in conn.audio_chunks)
                conn.audio_chunks.clear()

                import os, time, subprocess
                os.makedirs("debug_audio", exist_ok=True)
                ts = time.strftime("%H%M%S")
                pcm_path = f"debug_audio/audio_{ts}.pcm"
                with open(pcm_path, "wb") as f:
                    f.write(audio_bytes)
                wav_path = f"debug_audio/audio_{ts}.wav"
                subprocess.run([
                    "ffmpeg", "-y", "-f", "s16le", "-ar", "16000", "-ac", "1",
                    "-i", pcm_path, wav_path
                ], capture_output=True)
                print(f"[DEBUG] Saved: {pcm_path} ({len(audio_bytes)} bytes) -> {wav_path}")

                await manager.send_json(ws, {"type": "status", "message": "recognizing"})

                async with async_session_factory() as db:
                    try:
                        async for event in pipeline.speech_pipeline_stream(
                            db, audio_bytes, "pcm", agent_uuid, conn.conversation_id,
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
                                break

                            elif event_type == "audio_chunk":
                                await manager.send_json(ws, {
                                    "type": "audio_chunk",
                                    "content": event["content"],
                                })

                            elif event_type == "audio_done":
                                conn.conversation_id = uuid_mod.UUID(event["conversation_id"])
                                await manager.send_json(ws, {
                                    "type": "audio_done",
                                    "audioFormat": event["audio_format"],
                                    "audioError": event.get("audio_error", ""),
                                    "conversationId": event["conversation_id"],
                                })

                            elif event_type == "done":
                                pass

                    except Exception as e:
                        await manager.send_json(ws, {"type": "error", "message": str(e)})

            elif msg_type == "ping":
                await manager.send_json(ws, {"type": "pong"})

            elif msg_type == "text_chat":
                text = msg.get("text", "").strip()
                if not text:
                    continue

                await manager.send_json(ws, {"type": "status", "message": "thinking"})

                async with async_session_factory() as db:
                    try:
                        async for event in pipeline.chat_pipeline_stream(
                            db, text, agent_uuid, conn.conversation_id,
                        ):
                            event_type = event["type"]

                            if event_type == "text_chunk":
                                await manager.send_json(ws, {
                                    "type": "text_chunk",
                                    "content": event["content"],
                                })

                            elif event_type == "error":
                                await manager.send_json(ws, {
                                    "type": "error",
                                    "message": event["message"],
                                })
                                break

                            elif event_type == "audio_chunk":
                                await manager.send_json(ws, {
                                    "type": "audio_chunk",
                                    "content": event["content"],
                                })

                            elif event_type == "audio_done":
                                conn.conversation_id = uuid_mod.UUID(event["conversation_id"])
                                await manager.send_json(ws, {
                                    "type": "audio_done",
                                    "audioFormat": event["audio_format"],
                                    "audioError": event.get("audio_error", ""),
                                    "conversationId": event["conversation_id"],
                                })

                            elif event_type == "done":
                                pass

                    except Exception as e:
                        await manager.send_json(ws, {"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.disconnect(ws)
