# type: ignore
import asyncio
from collections.abc import AsyncGenerator

import dashscope
from dashscope.audio.tts_v2 import AudioFormat, ResultCallback, SpeechSynthesizer


async def synthesize_speech(
    text: str,
    voice_name: str,
    speed: float = 1.0,
    volume: float = 1.0,
    pitch: float = 1.0,
) -> bytes:
    dashscope.base_websocket_api_url = (
        "wss://dashscope.aliyuncs.com/api-ws/v1/inference"
    )

    loop = asyncio.get_running_loop()

    def _call():
        synthesizer = SpeechSynthesizer(
            model="cosyvoice-v3-flash",
            voice=voice_name,
            format=AudioFormat.MP3_22050HZ_MONO_256KBPS,
            speech_rate=speed,
            volume=int(volume * 50),
            pitch_rate=pitch,
        )
        return synthesizer.call(text)

    result = await loop.run_in_executor(None, _call)
    if not isinstance(result, bytes):
        raise RuntimeError("TTS 未返回有效音频数据")
    return result


async def synthesize_speech_streaming(
    text: str,
    voice_name: str,
    speed: float = 1.0,
    volume: float = 1.0,
    pitch: float = 1.0,
) -> AsyncGenerator[bytes, None]:
    dashscope.base_websocket_api_url = (
        "wss://dashscope.aliyuncs.com/api-ws/v1/inference"
    )

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    class StreamCallback(ResultCallback):
        def on_data(self, data: bytes) -> None:
            asyncio.run_coroutine_threadsafe(queue.put(("chunk", data)), loop)

        def on_complete(self):
            asyncio.run_coroutine_threadsafe(queue.put(("done", None)), loop)

        def on_error(self, message: str):
            asyncio.run_coroutine_threadsafe(queue.put(("error", message)), loop)

    def _tts_run():
        callback = StreamCallback()
        synthesizer = SpeechSynthesizer(
            model="cosyvoice-v3-flash",
            voice=voice_name,
            format=AudioFormat.PCM_22050HZ_MONO_16BIT,
            speech_rate=speed,
            volume=int(volume * 50),
            pitch_rate=pitch,
            callback=callback,
        )
        synthesizer.streaming_call(text)
        synthesizer.streaming_complete()

    loop.run_in_executor(None, _tts_run)

    while True:
        msg_type, data = await queue.get()
        if msg_type == "chunk":
            yield data
        elif msg_type == "error":
            raise RuntimeError(f"TTS streaming error: {data}")
        elif msg_type == "done":
            return
