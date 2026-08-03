import uuid
import io
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import aiohttp
from pydub import AudioSegment
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.voiceprint import VoiceprintSpeaker
from src.schemas.voiceprint import VoiceprintSpeakerResponse
from src.config import settings


def _to_wav_16k(audio_data: bytes) -> bytes | None:
    """将任意格式音频转换为 16kHz 单声道 16bit WAV（voiceprint-api 要求的格式）。

    返回转换后的 WAV 字节；转换失败返回 None。
    """
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_data))
        if len(audio) < 500:
            print(f"[voiceprint] 警告: 音频过短 {len(audio)}ms，注册可能失败")
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        buf = io.BytesIO()
        audio.export(buf, format="wav")
        return buf.getvalue()
    except Exception as e:
        print(f"[voiceprint] 音频转码失败: {e}")
        return None


async def list_speakers(db: AsyncSession) -> list[VoiceprintSpeakerResponse]:
    result = await db.execute(select(VoiceprintSpeaker).order_by(VoiceprintSpeaker.created_at.desc()))
    speakers = result.scalars().all()
    return [_to_response(s) for s in speakers]


async def register_speaker(
    db: AsyncSession,
    name: str,
    description: str,
    audio_data: bytes,
    voiceprint_url: str = "",
) -> VoiceprintSpeakerResponse:
    # 1. 保存到本地数据库
    speaker = VoiceprintSpeaker(
        name=name,
        description=description,
        registered_at=datetime.now().strftime("%Y-%m-%d"),
        sample_count=1,
    )
    db.add(speaker)
    await db.commit()
    await db.refresh(speaker)

    # 2. 如果配置了声纹 API，同步注册到外部声纹服务
    if voiceprint_url and audio_data:
        await _register_with_external_api(
            audio_data=audio_data,
            speaker_id=str(speaker.id),
            voiceprint_url=voiceprint_url,
        )

    return _to_response(speaker)


async def delete_speaker(db: AsyncSession, speaker_id: uuid.UUID) -> bool:
    result = await db.execute(select(VoiceprintSpeaker).where(VoiceprintSpeaker.id == speaker_id))
    speaker = result.scalar_one_or_none()
    if not speaker:
        return False

    # 同步删除外部 voiceprint-api 中的声纹
    if settings.voiceprint_url:
        await _delete_from_external_api(str(speaker_id), settings.voiceprint_url)

    await db.delete(speaker)
    await db.commit()
    return True


async def get_speaker_map(db: AsyncSession) -> dict[str, dict[str, str]]:
    """获取所有说话人的 id → {name, description} 映射，用于声纹识别时查找。"""
    result = await db.execute(select(VoiceprintSpeaker))
    speakers = result.scalars().all()
    return {
        str(s.id): {"name": s.name, "description": s.description or ""}
        for s in speakers
    }


async def _register_with_external_api(
    audio_data: bytes,
    speaker_id: str,
    voiceprint_url: str,
) -> bool:
    try:
        parsed = urlparse(voiceprint_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        query_params = parse_qs(parsed.query)
        api_key = query_params.get("key", [""])[0]

        if not api_key:
            print("[voiceprint] 未配置 API key，跳过外部注册")
            return False

        register_url = f"{base_url}/voiceprint/register"
        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        # voiceprint-api 只接受标准 16kHz 单声道 WAV，先把上传音频统一转码
        wav_data = _to_wav_16k(audio_data)
        if wav_data is None:
            print("[voiceprint] 音频转码失败，跳过外部注册")
            return False

        data = aiohttp.FormData()
        data.add_field("speaker_id", speaker_id)
        data.add_field("file", wav_data, filename="voice.wav", content_type="audio/wav")

        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(register_url, headers=headers, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"[voiceprint] 外部注册成功: speaker_id={speaker_id}, response={result}")
                    return True
                else:
                    text = await response.text()
                    print(f"[voiceprint] 外部注册失败: HTTP {response.status}, {text}")
                    return False

    except aiohttp.ClientError as e:
        print(f"[voiceprint] 外部注册网络错误: {e}")
        return False
    except Exception as e:
        print(f"[voiceprint] 外部注册异常: {e}")
        return False


def _to_response(s: VoiceprintSpeaker) -> VoiceprintSpeakerResponse:
    return VoiceprintSpeakerResponse(
        id=s.id,
        name=s.name,
        description=s.description or "",
        registered_at=s.registered_at,
        sample_count=s.sample_count,
    )


async def _delete_from_external_api(speaker_id: str, voiceprint_url: str) -> bool:
    """同步删除外部 voiceprint-api 中的声纹。"""
    try:
        parsed = urlparse(voiceprint_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        query_params = parse_qs(parsed.query)
        api_key = query_params.get("key", [""])[0]

        if not api_key:
            print("[voiceprint] 未配置 API key，跳过外部删除")
            return False

        delete_url = f"{base_url}/voiceprint/{speaker_id}"
        headers = {"Authorization": f"Bearer {api_key}"}

        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.delete(delete_url, headers=headers) as response:
                if response.status == 200:
                    print(f"[voiceprint] 外部删除成功: speaker_id={speaker_id}")
                    return True
                else:
                    text = await response.text()
                    print(f"[voiceprint] 外部删除失败: HTTP {response.status}, {text}")
                    return False
    except aiohttp.ClientError as e:
        print(f"[voiceprint] 外部删除网络错误: {e}")
        return False
    except Exception as e:
        print(f"[voiceprint] 外部删除异常: {e}")
        return False
