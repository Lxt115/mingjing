import json
import asyncio
import time
from opuslib_next import Encoder, Decoder
from opuslib_next import constants
from fastapi import WebSocket, WebSocketDisconnect

from src.ws.manager import manager
from src.database import async_session_factory
from src.services import pipeline
from src.models.agent import Agent
from src.providers.stt.bailian import StreamingBailianSTT
from sqlalchemy import select

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
    opus_chunks = []  # raw Opus bytes from device（仅用于统计）
    pipeline_task: asyncio.Task | None = None  # 当前 pipeline 异步任务，用于打断
    stt_session: StreamingBailianSTT | None = None  # 流式 STT 会话，失败时置 None 回退批式
    decoder: Decoder | None = None  # 逐帧解码器（录音期间复用）
    all_pcm = bytearray()  # 累积 PCM，用于声纹识别/批式 STT 兜底
    frame_count = 0

    async def cancel_pipeline():
        """取消正在运行的 pipeline 任务"""
        nonlocal pipeline_task
        if pipeline_task and not pipeline_task.done():
            pipeline_task.cancel()
            try:
                await pipeline_task
            except asyncio.CancelledError:
                pass
        pipeline_task = None

    try:
        while True:
            raw = await ws.receive()

            if raw["type"] == "websocket.disconnect":
                break

            # ── Binary frame: Opus audio from device ──
            if "bytes" in raw and raw["bytes"] is not None:
                if is_recording:
                    opus_chunks.append(raw["bytes"])
                    # 逐帧解码 → 累积 PCM（声纹/批式兜底）+ 实时喂给流式 STT
                    if decoder is not None:
                        try:
                            pcm = decoder.decode(raw["bytes"], OPUS_FRAME_SAMPLES)
                        except Exception:
                            pcm = b""
                        if pcm:
                            all_pcm.extend(pcm)
                            frame_count += 1
                            if stt_session is not None:
                                try:
                                    await stt_session.send_audio(pcm)
                                except Exception as e:
                                    print(f"[streaming-stt] send 失败，回退批式: {type(e).__name__}: {e}")
                                    try:
                                        await stt_session.close()
                                    except Exception:
                                        pass
                                    stt_session = None
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
                # 先取消旧的 pipeline（如果正在运行）
                await cancel_pipeline()
                is_recording = True
                opus_chunks.clear()
                all_pcm.clear()
                frame_count = 0
                decoder = Decoder(OPUS_SAMPLE_RATE, OPUS_CHANNELS)

                # 建立流式 STT 会话（连接失败自动回退批式识别）
                stt_session = StreamingBailianSTT()
                if stt_session.enabled:
                    try:
                        await stt_session.connect()
                        print("[streaming-stt] 会话已连接，开始边收边识别")
                    except Exception as e:
                        print(f"[streaming-stt] 连接失败，回退批式: {type(e).__name__}: {e}")
                        try:
                            await stt_session.close()
                        except Exception:
                            pass
                        stt_session = None
                else:
                    stt_session = None
                await manager.send_json(ws, {"type": "status", "message": "recording"})

            elif msg_type == "abort":
                # 打断：取消正在运行的 pipeline，并关闭流式 STT 会话
                await cancel_pipeline()
                if stt_session is not None:
                    try:
                        await stt_session.close()
                    except Exception:
                        pass
                    stt_session = None
                await manager.send_json(ws, {"type": "abort"})

            elif msg_type == "audio_end":
                is_recording = False
                if not opus_chunks:
                    await manager.send_json(ws, {"type": "status", "message": "no audio"})
                    continue

                # 先取消可能还在运行的旧 pipeline
                await cancel_pipeline()

                # PCM 已在录音期间逐帧解码累积
                audio_bytes = bytes(all_pcm)
                total_ms = len(audio_bytes) // 2 * 1000 // OPUS_SAMPLE_RATE
                print(f"[DEBUG] Opus decode: {frame_count} frames → {len(audio_bytes)} bytes PCM (~{total_ms}ms)")
                opus_chunks.clear()

                if not audio_bytes:
                    await manager.send_json(ws, {"type": "error", "message": "Opus decode failed"})
                    continue

                if total_ms < 200:
                    # 录音过短（误触/空录）：跳过 STT 与 pipeline，立即回到空闲，避免 EmptyAudio 空转数秒
                    print(f"[voice] 录音过短 {total_ms}ms，忽略本次录音")
                    await manager.send_json(ws, {"type": "status", "message": "no audio"})
                    continue

                # 流式 STT：发送 finish-task 拿最终文本（通常几百 ms），失败则回退批式
                pre_text: str | None = None
                if stt_session is not None:
                    try:
                        t0 = time.perf_counter()
                        final = await stt_session.finalize(timeout=3.5)
                        print(f"[streaming-stt] finalize 耗时 {(time.perf_counter() - t0) * 1000:.0f}ms → {final[:40]!r}")
                        if final and not final.startswith("["):
                            pre_text = final
                    except Exception as e:
                        print(f"[streaming-stt] finalize 失败，回退批式: {type(e).__name__}: {e}")
                    finally:
                        try:
                            await stt_session.close()
                        except Exception:
                            pass
                    stt_session = None

                await manager.send_json(ws, {"type": "status", "message": "recognizing"})

                # ── 运行 pipeline 作为可取消的异步任务 ──
                async def run_pipeline():
                    encoder = Encoder(OPUS_SAMPLE_RATE, OPUS_CHANNELS, constants.APPLICATION_AUDIO)
                    encoder.bitrate = 24000
                    encoder.complexity = 10
                    encoder.signal = constants.SIGNAL_VOICE

                    frame_size = OPUS_FRAME_SAMPLES * 2  # 1920 bytes per 60ms frame
                    pcm_buffer = bytearray()

                    async with async_session_factory() as db:
                        # 通过 agent 获取 user_id
                        agent_result = await db.execute(select(Agent).where(Agent.id == agent_uuid))
                        agent = agent_result.scalar_one_or_none()
                        pipeline_user_id = agent.user_id if agent else None

                        # 通过 nginx 代理时，从 X-Real-IP 获取真实客户端 IP
                        real_ip = ws.headers.get("x-real-ip") or ws.client.host
                        async for event in pipeline.speech_pipeline_stream(
                            db, audio_bytes, "pcm", agent_uuid, conn.conversation_id,
                            client_ip=real_ip, user_id=pipeline_user_id,
                            pre_transcribed_text=pre_text,
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

                            elif event_type == "audio_chunk":
                                import base64 as b64
                                pcm_data = b64.b64decode(event["content"])

                                pcm_buffer.extend(pcm_data)
                                while len(pcm_buffer) >= frame_size:
                                    pcm_frame = bytes(pcm_buffer[:frame_size])
                                    del pcm_buffer[:frame_size]
                                    try:
                                        opus_frame = encoder.encode(pcm_frame, OPUS_FRAME_SAMPLES)
                                        if opus_frame:
                                            await ws.send_bytes(opus_frame)
                                            await asyncio.sleep(0.06)
                                    except Exception:
                                        pass

                            elif event_type == "audio_done":
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

                # 启动 pipeline 任务
                pipeline_task = asyncio.create_task(run_pipeline())
                try:
                    await pipeline_task
                except asyncio.CancelledError:
                    print("[voice] pipeline cancelled by abort")
                except Exception as e:
                    print(f"[voice] pipeline error: {type(e).__name__}: {e}")
                    await manager.send_json(ws, {"type": "error", "message": str(e)})
                finally:
                    pipeline_task = None

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[voice] error: {e}")
    finally:
        if stt_session is not None:
            try:
                await stt_session.close()
            except Exception:
                pass
            stt_session = None
        manager.disconnect(ws)
