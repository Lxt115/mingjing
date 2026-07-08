"""百炼 ASR 提供商 —— 基于阿里百炼 paraformer-realtime-v2 模型。

使用 WebSocket duplex 协议进行语音识别。
优化：PCM 输入直接内存转 WAV，跳过 ffmpeg 以降低延迟。
"""

import io
import asyncio
import json
import uuid
import wave
import websockets
import subprocess
import tempfile
import os

from src.config import settings
from src.providers.stt.base import STTProvider


def _pcm_to_wav_bytes(pcm_data: bytes, sample_rate: int = 16000, channels: int = 1, bits: int = 16) -> bytes:
    """在内存中将 PCM 数据转换为 WAV 格式，避免 ffmpeg 开销。"""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(bits // 8)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()


class BailianSTTProvider(STTProvider):
    async def transcribe(self, audio_bytes: bytes, audio_format: str = "webm", max_retries: int = 2) -> str:
        if not settings.dashscope_api_key:
            return "[百炼 STT 未配置 API Key]"

        tmp_input = None
        tmp_output = None

        try:
            wav_data: bytes

            # PCM 格式：内存直接转 WAV，跳过 ffmpeg
            if audio_format == "pcm":
                wav_data = _pcm_to_wav_bytes(audio_bytes)
            else:
                # 其他格式：通过 ffmpeg 转换
                tmp_input = tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False)
                tmp_input.write(audio_bytes)
                tmp_input.close()

                tmp_output = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                tmp_output.close()

                cmd = [
                    "ffmpeg", "-y", "-i", tmp_input.name,
                    "-ar", "16000", "-ac", "1", "-f", "wav",
                    tmp_output.name,
                ]
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: subprocess.run(cmd, capture_output=True, timeout=30),
                )
                if result.returncode != 0:
                    stderr = result.stderr.decode(errors="ignore")[:200] if result.stderr else ""
                    return f"[百炼 STT 音频转换失败: {stderr}]"

                with open(tmp_output.name, "rb") as f:
                    wav_data = f.read()

            # 带重试的识别
            last_error = ""
            for attempt in range(max_retries):
                try:
                    text = await self._recognize_via_websocket(wav_data)
                    if text and not text.startswith("["):
                        return text
                    last_error = text
                except Exception as e:
                    last_error = f"[百炼 STT 第{attempt+1}次: {type(e).__name__}: {e}]"
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.5)

            return last_error or "[百炼 STT 未识别到文字]"

        except Exception as e:
            return f"[百炼 STT 异常: {type(e).__name__}: {e}]"
        finally:
            _cleanup_temp(tmp_input)
            _cleanup_temp(tmp_output)

    async def _recognize_via_websocket(self, wav_data: bytes) -> str:
        task_id = uuid.uuid4().hex[:32]
        ws_url = "wss://dashscope.aliyuncs.com/api-ws/v1/inference/"
        headers = {
            "Authorization": f"Bearer {settings.dashscope_api_key}"
        }

        try:
            async with websockets.connect(ws_url, extra_headers=headers) as ws:
                run_task_msg = {
                    "header": {
                        "action": "run-task",
                        "task_id": task_id,
                        "streaming": "duplex"
                    },
                    "payload": {
                        "task_group": "audio",
                        "task": "asr",
                        "function": "recognition",
                        "model": "paraformer-realtime-v2",
                        "parameters": {
                            "format": "wav",
                            "sample_rate": 16000
                        },
                        "input": {}
                    }
                }
                await ws.send(json.dumps(run_task_msg))

                task_started = False
                sentences = {}

                while True:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=15)
                    except asyncio.TimeoutError:
                        break

                    try:
                        data = json.loads(msg)
                        event = data.get("header", {}).get("event", "")

                        if event == "task-started":
                            task_started = True
                            await ws.send(wav_data)

                            finish_task_msg = {
                                "header": {
                                    "action": "finish-task",
                                    "task_id": task_id,
                                    "streaming": "duplex"
                                },
                                "payload": {
                                    "input": {}
                                }
                            }
                            await ws.send(json.dumps(finish_task_msg))

                        elif event == "result-generated":
                            sentence = data.get("payload", {}).get("output", {}).get("sentence", {})
                            text = sentence.get("text", "")
                            sid = sentence.get("sentence_id", len(sentences))
                            if text:
                                sentences[sid] = text

                        elif event == "task-finished":
                            break

                        elif event == "task-failed":
                            error_msg = data.get("header", {}).get("error_message", "Unknown error")
                            return f"[百炼 STT 任务失败: {error_msg}]"

                    except json.JSONDecodeError:
                        pass

                recognized_text = "".join(sentences[sid] for sid in sorted(sentences))
                return recognized_text

        except Exception as e:
            return f"[百炼 STT WebSocket 异常: {type(e).__name__}: {e}]"


def _cleanup_temp(tmp_file) -> None:
    """安全删除临时文件。"""
    if tmp_file and os.path.exists(tmp_file.name):
        try:
            os.unlink(tmp_file.name)
        except Exception:
            pass
