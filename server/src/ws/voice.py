import json
import asyncio
from opuslib_next import Encoder, Decoder
from opuslib_next import constants
from fastapi import WebSocket, WebSocketDisconnect

from src.ws.manager import manager
from src.database import async_session_factory
from src.services import pipeline

# 与固件 OPUS_SAMPLE_RATE / OPUS_FRAME_DURATION_MS 保持一致
OPUS_SAMPLE_RATE = 16000
OPUS_CHANNELS = 1
OPUS_FRAME_SAMPLES = OPUS_SAMPLE_RATE * 60 // 1000  # 960 samples per 60ms frame


async def handle_voice(ws: WebSocket, agent_id: str):
    import uuid as uuid_mod
    try:
        agent_uuid = uuid_mod.UUID(agent_id)
    except ValueError:
        await ws.close(code=1008, reason="invalid agent_id")
        return

    conn = await manager.connect(ws, agent_uuid)
    await manager.send_json(ws, {"type": "welcome", "agent_id": str(agent_uuid)})

    is_recording = False
    opus_chunks = []  # raw Opus bytes from device

    try:
        while True:
            raw = await ws.receive()

            if raw["type"] == "websocket.disconnect":
                break

            # ── Binary frame: Opus audio from device ──
            if "bytes" in raw and raw["bytes"] is not None:
                if is_recording:
                    opus_chunks.append(raw["bytes"])
                continue

            # ── Text frame: JSON control message ──
            if "text" not in raw:
                continue

            try:
                msg = json.loads(raw["text"])
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type", "")

            if msg_type == "audio_start":
                is_recording = True
                opus_chunks.clear()
                await manager.send_json(ws, {"type": "status", "message": "recording"})

            elif msg_type == "audio_end":
                is_recording = False
                if not opus_chunks:
                    await manager.send_json(ws, {"type": "status", "message": "no audio"})
                    continue

                # Decode each Opus frame → PCM (each chunk is one 60ms frame)
                decoder = Decoder(OPUS_SAMPLE_RATE, OPUS_CHANNELS)
                pcm_parts = []
                frame_count = len(opus_chunks)
                for chunk in opus_chunks:
                    try:
                        decoded = decoder.decode(chunk, OPUS_FRAME_SAMPLES)
                        pcm_parts.append(decoded)
                    except Exception:
                        pass
                opus_chunks.clear()

                audio_bytes = b"".join(pcm_parts)
                total_ms = len(audio_bytes) // 2 * 1000 // OPUS_SAMPLE_RATE
                print(f"[DEBUG] Opus decode: {frame_count} frames → {len(audio_bytes)} bytes PCM (~{total_ms}ms)")

                if not audio_bytes:
                    await manager.send_json(ws, {"type": "error", "message": "Opus decode failed"})
                    continue

                await manager.send_json(ws, {"type": "status", "message": "recognizing"})

                # xiaozhi pattern: APPLICATION_AUDIO, bitrate=24000, complexity=10, SIGNAL_VOICE
                encoder = Encoder(OPUS_SAMPLE_RATE, OPUS_CHANNELS, constants.APPLICATION_AUDIO)
                encoder.bitrate = 24000
                encoder.complexity = 10
                encoder.signal = constants.SIGNAL_VOICE

                # 缓冲区：存放跨 chunk 未对齐的 PCM 剩余数据，避免尾部截断
                frame_size = OPUS_FRAME_SAMPLES * 2  # 1920 bytes per 60ms frame
                pcm_buffer = bytearray()

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
                                # event["content"] is base64-encoded PCM from TTS
                                import base64 as b64
                                pcm_bytes = b64.b64decode(event["content"])

                                # 追加到缓冲区，积累成完整帧再编码
                                pcm_buffer.extend(pcm_bytes)
                                while len(pcm_buffer) >= frame_size:
                                    pcm_frame = bytes(pcm_buffer[:frame_size])
                                    del pcm_buffer[:frame_size]
                                    try:
                                        opus_frame = encoder.encode(pcm_frame, OPUS_FRAME_SAMPLES)
                                        if opus_frame:
                                            await ws.send_bytes(opus_frame)
                                            # 速率控制：每帧60ms，匹配ESP32 I2S播放时钟
                                            await asyncio.sleep(0.06)
                                    except Exception:
                                        pass

                            elif event_type == "audio_done":
                                # 刷新缓冲区尾部：用静音补齐最后一个不完整帧
                                if len(pcm_buffer) > 0:
                                    padded = bytes(pcm_buffer) + b'\x00' * (frame_size - len(pcm_buffer))
                                    try:
                                        opus_frame = encoder.encode(padded, OPUS_FRAME_SAMPLES)
                                        if opus_frame:
                                            await ws.send_bytes(opus_frame)
                                    except Exception:
                                        pass

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
    except Exception as e:
        print(f"[voice] error: {e}")
    finally:
        manager.disconnect(ws)
