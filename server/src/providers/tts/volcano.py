"""火山 TTS 提供商 —— 基于豆包语音合成模型 2.0 (seed-tts-2.0)。

- synthesize: 非流式，返回 MP3（用于试听）
- synthesize_streaming: 流式，返回 PCM 16kHz（用于实时语音输出）
"""

import asyncio
import base64
import json
import uuid
from collections.abc import AsyncGenerator

import httpx

from src.config import settings
from src.providers.tts.base import TTSProvider


class VolcanoTTSProvider(TTSProvider):
    """火山引擎豆包语音合成 2.0"""

    async def synthesize(
        self,
        text: str,
        voice_name: str = "zh_female_vv_uranus_bigtts",
        speed: float = 1.0,
        volume: float = 1.0,
        pitch: float = 1.0,
    ) -> bytes:
        if not settings.volcano_api_key:
            raise RuntimeError("volcano_api_key 未配置，无法使用火山 TTS")

        reqid = uuid.uuid4().hex[:32]
        url = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
        headers = {
            "X-Api-Key": settings.volcano_api_key,
            "X-Api-Resource-Id": "seed-tts-2.0",
            "X-Api-Request-Id": reqid,
            "Content-Type": "application/json",
        }
        payload = {
            "req_params": {
                "text": text,
                "speaker": voice_name,
                "audio_params": {
                    "format": "mp3",
                    "sample_rate": 24000,
                    "speech_rate": int((speed - 1.0) * 100),
                    "loudness_rate": int((volume - 1.0) * 100),
                },
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise RuntimeError(f"火山 TTS HTTP {resp.status_code}: {body.decode(errors='ignore')[:300]}")

                audio_chunks: list[bytes] = []
                async for line in resp.aiter_lines():
                    line_s = line.strip()
                    if not line_s:
                        continue
                    try:
                        obj = json.loads(line_s)
                        audio_b64 = obj.get("data", "") or ""
                        if audio_b64:
                            audio_chunks.append(base64.b64decode(audio_b64))
                    except json.JSONDecodeError:
                        pass

                if not audio_chunks:
                    raise RuntimeError("火山 TTS 未返回有效音频数据")
                return b"".join(audio_chunks)

    async def synthesize_streaming(
        self,
        text: str,
        voice_name: str = "zh_female_vv_uranus_bigtts",
        speed: float = 1.0,
        volume: float = 1.0,
        pitch: float = 1.0,
    ) -> AsyncGenerator[bytes, None]:
        if not settings.volcano_api_key:
            raise RuntimeError("volcano_api_key 未配置，无法使用火山 TTS")

        reqid = uuid.uuid4().hex[:32]
        url = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
        headers = {
            "X-Api-Key": settings.volcano_api_key,
            "X-Api-Resource-Id": "seed-tts-2.0",
            "X-Api-Request-Id": reqid,
            "Content-Type": "application/json",
        }
        payload = {
            "req_params": {
                "text": text,
                "speaker": voice_name,
                "audio_params": {
                    "format": "pcm",
                    "sample_rate": 16000,
                    "speech_rate": int((speed - 1.0) * 100),
                    "loudness_rate": int((volume - 1.0) * 100),
                },
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise RuntimeError(f"火山 TTS HTTP {resp.status_code}: {body.decode(errors='ignore')[:300]}")

                async for line in resp.aiter_lines():
                    line_s = line.strip()
                    if not line_s:
                        continue
                    try:
                        obj = json.loads(line_s)
                        audio_b64 = obj.get("data", "") or ""
                        if audio_b64:
                            yield base64.b64decode(audio_b64)
                    except json.JSONDecodeError:
                        pass
