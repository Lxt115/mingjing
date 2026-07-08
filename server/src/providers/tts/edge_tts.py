"""Edge TTS 提供商 —— 基于 edge-tts 库，免费无需 API Key。

- synthesize: 非流式，返回完整 MP3 bytes
- synthesize_streaming: 流式，逐 chunk 返回 PCM bytes
"""

import io
from collections.abc import AsyncGenerator

import edge_tts

from src.providers.tts.base import TTSProvider


class EdgeTTSProvider(TTSProvider):
    async def synthesize(
        self,
        text: str,
        voice_name: str = "zh-CN-XiaoxiaoNeural",
        speed: float = 1.0,
        volume: float = 1.0,
        pitch: float = 1.0,
    ) -> bytes:
        rate_str = _rate_str(speed)
        pitch_str = _pitch_str(pitch)

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice_name,
            rate=rate_str,
            pitch=pitch_str,
        )

        audio_bytes = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes.write(chunk["data"])

        full_audio = audio_bytes.getvalue()
        if not full_audio:
            raise RuntimeError("Edge TTS 未返回有效音频数据")
        return full_audio

    async def synthesize_streaming(
        self,
        text: str,
        voice_name: str = "zh-CN-XiaoxiaoNeural",
        speed: float = 1.0,
        volume: float = 1.0,
        pitch: float = 1.0,
    ) -> AsyncGenerator[bytes, None]:
        rate_str = _rate_str(speed)
        pitch_str = _pitch_str(pitch)

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice_name,
            rate=rate_str,
            pitch=pitch_str,
        )

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]


def _rate_str(speed: float) -> str:
    """将 speed 倍率转换为 edge-tts rate 字符串（+-N%）。"""
    pct = int((speed - 1.0) * 100)
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct}%"


def _pitch_str(pitch: float) -> str:
    """将 pitch 倍率转换为 edge-tts pitch 字符串（+-NHz）。"""
    pct = int((pitch - 1.0) * 100)
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct}Hz"
