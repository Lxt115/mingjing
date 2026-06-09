import io
import asyncio
import json
import uuid
import websockets
import subprocess
import tempfile
import os

from src.config import settings
from src.providers.stt.base import STTProvider


class BailianSTTProvider(STTProvider):
    async def transcribe(self, audio_bytes: bytes, audio_format: str = "webm") -> str:
        if not settings.dashscope_api_key:
            return "[百炼 STT 未配置 API Key]"

        tmp_input = None
        tmp_output = None

        try:
            tmp_input = tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False)
            tmp_input.write(audio_bytes)
            tmp_input.close()

            tmp_output = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_output.close()

            if audio_format == "pcm":
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "s16le", "-ar", "16000", "-ac", "1",
                    "-i", tmp_input.name,
                    "-ar", "16000", "-ac", "1",
                    "-f", "wav",
                    tmp_output.name
                ]
            else:
                cmd = [
                    "ffmpeg", "-y", "-i", tmp_input.name,
                    "-ar", "16000", "-ac", "1",
                    "-f", "wav",
                    tmp_output.name
                ]
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True)
            )
            if result.returncode != 0:
                return "[百炼 STT 音频转换失败]"

            with open(tmp_output.name, "rb") as f:
                wav_data = f.read()

            text = await self._recognize_via_websocket(wav_data)
            return text if text else "[百炼 STT 未识别到文字]"

        except Exception as e:
            return f"[百炼 STT 异常: {type(e).__name__}: {e}]"
        finally:
            if tmp_input and os.path.exists(tmp_input.name):
                try:
                    os.unlink(tmp_input.name)
                except Exception:
                    pass
            if tmp_output and os.path.exists(tmp_output.name):
                try:
                    os.unlink(tmp_output.name)
                except Exception:
                    pass

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
