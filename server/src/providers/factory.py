from src.config import settings
from src.providers.stt.base import STTProvider
from src.providers.llm.base import LLMProvider
from src.providers.tts.base import TTSProvider


_stt: STTProvider | None = None
_llm: LLMProvider | None = None
_tts: TTSProvider | None = None


def get_stt() -> STTProvider:
    global _stt
    if _stt is None:
        from src.providers.stt.bailian import BailianSTTProvider
        _stt = BailianSTTProvider()
    return _stt


def get_llm() -> LLMProvider:
    global _llm
    if _llm is None:
        from src.providers.llm.bailian import BailianLLMProvider
        _llm = BailianLLMProvider()
    return _llm


def get_tts() -> TTSProvider:
    global _tts
    if _tts is None:
        from src.providers.tts.bailian import BailianTTSProvider
        _tts = BailianTTSProvider()
    return _tts
