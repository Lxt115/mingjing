"""百炼 ASR 提供商 —— 基于阿里百炼 fun-asr-realtime 模型。

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


def _ws_connect(url, headers):
    """兼容 websockets v14+/v16 的 connect 调用"""
    import inspect
    sig = inspect.signature(websockets.connect)
    if "additional_headers" in sig.parameters:
        return websockets.connect(url, additional_headers=headers)
    else:
        return websockets.connect(url, extra_headers=headers)


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
            async with _ws_connect(ws_url, headers) as ws:
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
                        "model": "fun-asr-realtime",
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
                            # 分块发送大音频（每块 128KB，避免超过服务端消息限制）
                            chunk_size = 128 * 1024
                            for i in range(0, len(wav_data), chunk_size):
                                await ws.send(wav_data[i:i + chunk_size])
                                await asyncio.sleep(0.01)

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


class StreamingBailianSTT:
    """百炼 fun-asr-realtime 流式识别会话（边收边识别）。

    与批式 transcribe 共用同一个 duplex WebSocket 协议，区别在于：
    - 音频帧随到随发（原始 PCM，format=pcm）
    - 识别结果实时回流（result-generated 事件）
    - audio_end 时发送 finish-task 拿最终文本，通常几百毫秒内完成
    任何一步失败都返回以 '[' 开头的错误描述，由调用方回退到批式识别。
    """

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or settings.dashscope_api_key
        self._ws = None
        self._task_id = uuid.uuid4().hex[:32]
        self._sentences: dict[int, str] = {}
        self._pending = bytearray()  # 连接就绪前收到的音频帧缓存
        self._result_queue: asyncio.Queue = asyncio.Queue()
        self._reader_task: asyncio.Task | None = None
        self._ready = False
        self._closed = False

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def connect(self) -> None:
        """打开 WebSocket 并发起 run-task，等待 task-started。"""
        ws_url = "wss://dashscope.aliyuncs.com/api-ws/v1/inference/"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        self._ws = await _ws_connect(ws_url, headers).__aenter__()

        run_task_msg = {
            "header": {
                "action": "run-task",
                "task_id": self._task_id,
                "streaming": "duplex"
            },
            "payload": {
                "task_group": "audio",
                "task": "asr",
                "function": "recognition",
                "model": "fun-asr-realtime",
                "parameters": {
                    "format": "pcm",
                    "sample_rate": 16000
                },
                "input": {}
            }
        }
        await self._ws.send(json.dumps(run_task_msg))

        # 等待 task-started，期间收到的音频帧暂存，就绪后统一补发
        while True:
            try:
                msg = await asyncio.wait_for(self._ws.recv(), timeout=15)
            except asyncio.TimeoutError:
                raise TimeoutError("streaming stt: 等待 task-started 超时")
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                continue
            event = data.get("header", {}).get("event", "")
            if event == "task-started":
                self._ready = True
                break
            if event == "task-failed":
                raise RuntimeError(data.get("header", {}).get("error_message", "unknown"))

        if self._pending:
            await self._ws.send(bytes(self._pending))
            self._pending.clear()
        self._reader_task = asyncio.create_task(self._read_loop())

    async def send_audio(self, pcm: bytes) -> None:
        """发送一段 PCM 音频（16k/16bit/单声道）。连接未就绪时先缓存。"""
        if self._closed or not pcm:
            return
        if not self._ready:
            self._pending.extend(pcm)
            return
        await self._ws.send(pcm)

    async def _read_loop(self) -> None:
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(self._ws.recv(), timeout=30)
                except asyncio.TimeoutError:
                    continue
                try:
                    data = json.loads(msg)
                except json.JSONDecodeError:
                    continue
                event = data.get("header", {}).get("event", "")
                if event == "result-generated":
                    sentence = data.get("payload", {}).get("output", {}).get("sentence", {})
                    text = sentence.get("text", "")
                    sid = sentence.get("sentence_id", 0)
                    if text:
                        self._sentences[sid] = text
                        await self._result_queue.put(("partial", self._full_text()))
                elif event == "task-finished":
                    await self._result_queue.put(("final", self._full_text()))
                    break
                elif event == "task-failed":
                    await self._result_queue.put(("error", data.get("header", {}).get("error_message", "unknown")))
                    break
        except Exception as e:
            await self._result_queue.put(("error", f"{type(e).__name__}: {e}"))

    def _full_text(self) -> str:
        return "".join(self._sentences[sid] for sid in sorted(self._sentences))

    async def finalize(self, timeout: float = 4.0) -> str:
        """发送 finish-task，返回最终识别文本；失败返回以 '[' 开头的错误描述。"""
        if not self._ready:
            return "[百炼 STT 流式未就绪]"
        finish_task_msg = {
            "header": {
                "action": "finish-task",
                "task_id": self._task_id,
                "streaming": "duplex"
            },
            "payload": {"input": {}}
        }
        try:
            await self._ws.send(json.dumps(finish_task_msg))
            while True:
                kind, payload = await asyncio.wait_for(self._result_queue.get(), timeout=timeout)
                if kind == "partial":
                    continue
                if kind == "final":
                    return payload
                return f"[百炼 STT 流式失败: {payload}]"
        except asyncio.TimeoutError:
            return "[百炼 STT 流式 finalize 超时]"
        except Exception as e:
            return f"[百炼 STT 流式异常: {type(e).__name__}: {e}]"

    async def close(self) -> None:
        """关闭会话：取消读取任务并关闭 WebSocket。"""
        if self._closed:
            return
        self._closed = True
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except (asyncio.CancelledError, Exception):
                pass
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
        self._ws = None
