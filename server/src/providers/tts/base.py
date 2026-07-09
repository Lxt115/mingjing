from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(
        self, text: str, voice_name: str = "zh-CN-XiaoxiaoNeural",
        speed: float = 1.0, volume: float = 1.0, pitch: float = 1.0,
    ) -> bytes:
        ...

    @abstractmethod
    async def synthesize_streaming(
        self, text: str, voice_name: str = "zh-CN-XiaoxiaoNeural",
        speed: float = 1.0, volume: float = 1.0, pitch: float = 1.0,
    ) -> AsyncGenerator[bytes, None]:
        ...
