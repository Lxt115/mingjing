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
        _stt = _create_stt(settings.stt_provider)
    return _stt


def get_llm() -> LLMProvider:
    global _llm
    if _llm is None:
        _llm = _create_llm(settings.llm_provider)
    return _llm


def get_tts() -> TTSProvider:
    global _tts
    if _tts is None:
        _tts = _create_tts(settings.tts_provider)
    return _tts


def _create_stt(name: str) -> STTProvider:
    if name == "bailian":
        from src.providers.stt.bailian import BailianSTTProvider
        return BailianSTTProvider()
    else:
        raise ValueError(f"Unknown STT provider: {name}")


def _create_llm(name: str) -> LLMProvider:
    if name == "bailian":
        from src.providers.llm.bailian import BailianLLMProvider
        return BailianLLMProvider()
    elif name == "deepseek":
        from src.providers.llm.deepseek import DeepSeekLLMProvider
        return DeepSeekLLMProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {name}")


def _create_tts(name: str) -> TTSProvider:
    if name == "volcano":
        from src.providers.tts.volcano import VolcanoTTSProvider
        return VolcanoTTSProvider()
    elif name == "bailian":
        from src.providers.tts.bailian import BailianTTSProvider
        return BailianTTSProvider()
    else:
        raise ValueError(f"Unknown TTS provider: {name}")
