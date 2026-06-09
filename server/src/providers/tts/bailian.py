from collections.abc import AsyncGenerator

from src.config import settings
from src.providers.tts._synthesize import synthesize_speech, synthesize_speech_streaming
from src.providers.tts.base import TTSProvider


class BailianTTSProvider(TTSProvider):
    async def synthesize(
        self,
        text: str,
        voice_name: str = "longanhuan",
        speed: float = 1.0,
        volume: float = 1.0,
        pitch: float = 1.0,
    ) -> bytes:
        if not settings.dashscope_api_key:
            raise RuntimeError("dashscope_api_key 未配置，无法使用百炼 TTS")
        return await synthesize_speech(
            text=text,
            voice_name=voice_name,
            speed=speed,
            volume=volume,
            pitch=pitch,
        )

    async def synthesize_streaming(
        self,
        text: str,
        voice_name: str = "longanhuan",
        speed: float = 1.0,
        volume: float = 1.0,
        pitch: float = 1.0,
    ) -> AsyncGenerator[bytes, None]:
        if not settings.dashscope_api_key:
            raise RuntimeError("dashscope_api_key 未配置，无法使用百炼 TTS")
        async for chunk in synthesize_speech_streaming(
            text=text,
            voice_name=voice_name,
            speed=speed,
            volume=volume,
            pitch=pitch,
        ):
            yield chunk
