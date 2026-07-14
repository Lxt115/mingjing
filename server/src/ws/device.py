import json
import uuid as uuid_mod
import random
from datetime import datetime, timedelta, timezone
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.ws.manager import manager
from src.database import async_session_factory
from src.models.device import Device
from src.models.user import User

# ── 配对码存储（内存中）──
# { code: {"device_uuid": uuid, "digit_audios": [bytes], "created_at": datetime} }
_pair_codes: dict[str, dict] = {}
_PAIR_CODE_TIMEOUT_MINUTES = 5


def generate_pair_code(device_uuid: uuid_mod.UUID) -> str:
    """生成不重复的 4 位数字配对码。"""
    _clean_expired_codes()
    for _ in range(100):
        code = f"{random.randint(0, 9999):04d}"
        if code not in _pair_codes:
            _pair_codes[code] = {
                "device_uuid": device_uuid,
                "created_at": datetime.now(timezone.utc),
            }
            return code
    return f"{random.randint(0, 9999):04d}"


def get_device_by_code(code: str) -> uuid_mod.UUID | None:
    """通过配对码获取 device_uuid。"""
    _clean_expired_codes()
    entry = _pair_codes.get(code.strip())
    return entry["device_uuid"] if entry else None


def get_pair_audio(code: str) -> bytes | None:
    """获取配对码对应的完整音频数据。"""
    _clean_expired_codes()
    entry = _pair_codes.get(code.strip())
    if not entry:
        return None
    audios = entry.get("digit_audios", [])
    return b"".join(audios) if audios else None


def consume_pair_code(code: str) -> uuid_mod.UUID | None:
    """绑定用：获取并删除配对码条目。"""
    device_uuid = get_device_by_code(code)
    if device_uuid:
        _pair_codes.pop(code.strip(), None)
    return device_uuid


def _clean_expired_codes():
    now = datetime.now(timezone.utc)
    expired = [c for c, e in _pair_codes.items()
               if now - e["created_at"] > timedelta(minutes=_PAIR_CODE_TIMEOUT_MINUTES)]
    for c in expired:
        del _pair_codes[c]


def get_pair_digit_audio(code: str, index: int) -> bytes | None:
    """获取配对码第 index 位数字的音频。"""
    entry = _pair_codes.get(code.strip())
    if not entry:
        return None
    digit_audios = entry.get("digit_audios")
    if not digit_audios or index < 0 or index >= len(digit_audios):
        return None
    return digit_audios[index]


async def _generate_digit_audio(digit: str) -> bytes:
    """为单个数字生成 TTS 音频 (raw PCM 16kHz 16-bit mono)。"""
    text = digit  # 只念数字本身
    try:
        from src.providers.factory import get_tts
        tts = get_tts()
        pcm_chunks = []
        async for chunk in tts.synthesize_streaming(
            text=text,
            voice_name="zh_female_vv_uranus_bigtts",
            speed=1.0,
        ):
            pcm_chunks.append(chunk)
        return b"".join(pcm_chunks)
    except Exception as e:
        print(f"[pair_code] digit TTS failed: {e}")
        return b""


async def _generate_pair_audio(code: str) -> bytes:
    """调用 TTS 生成配对码全部数字语音列表。"""
    digit_audios = []
    for ch in code:
        pcm = await _generate_digit_audio(ch)
        digit_audios.append(pcm)
    return digit_audios


async def handle_device(ws: WebSocket, device_id: str):
    try:
        device_uuid = uuid_mod.UUID(device_id)
    except ValueError:
        await ws.close(code=1008, reason="invalid device_id")
        return

    async with async_session_factory() as db:
        result = await db.execute(
            select(Device).options(selectinload(Device.agent)).where(Device.id == device_uuid)
        )
        device = result.scalar_one_or_none()
        if not device:
            device = Device(
                id=device_uuid,
                name=f"设备-{str(device_uuid)[-4:]}",
                mac=str(device_uuid)[:17],
                status="pending",
                bind_code=None,
            )
            db.add(device)
            await db.commit()
            await db.refresh(device)
            agent_id = None
        else:
            agent_id = device.bound_agent_id
            device.status = "online"
            await db.commit()

    if not agent_id:
        # 设备未绑定：生成配对码 + TTS 语音
        pair_code = generate_pair_code(device_uuid)
        audio_pcm = await _generate_pair_audio(pair_code)

        # 存储每位数音频到配对码条目（供 /api/pair-audio/{code}/{index} 下载）
        entry = _pair_codes.get(pair_code)
        if entry:
            entry["digit_audios"] = audio_pcm  # list of 4 PCM byte chunks

        conn = await manager.connect(ws, None, device_uuid)

        # 只发送配对码（音频通过 HTTP 下载）
        await manager.send_json(ws, {
            "type": "pair_code",
            "code": pair_code,
        })
        print(f"[device] new device {str(device_uuid)[-8:]}, pair_code={pair_code}, audio={len(audio_pcm)} bytes")

        # 等第一条 device_info（兼容旧固件）
        try:
            while True:
                raw = await ws.receive()
                if raw["type"] == "websocket.disconnect":
                    return
                if "text" in raw:
                    try:
                        msg = json.loads(raw["text"])
                        if msg.get("type") == "device_info":
                            async with async_session_factory() as db2:
                                result = await db2.execute(select(Device).where(Device.id == device_uuid))
                                dev = result.scalar_one_or_none()
                                if dev and msg.get("bind_code"):
                                    dev.bind_code = msg["bind_code"]
                                    await db2.commit()
                            await manager.send_json(ws, {
                                "type": "welcome",
                                "device_id": str(device_uuid),
                                "agent_id": None,
                                "bind_code": msg.get("bind_code"),
                                "mac": device.mac,
                                "firmware_version": device.firmware_version,
                            })
                            break
                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        print(f"[device] device_info error: {e}")
        except WebSocketDisconnect:
            pass

        try:
            while True:
                raw = await ws.receive()
                if raw["type"] == "websocket.disconnect":
                    break
        except WebSocketDisconnect:
            pass
        finally:
            async with async_session_factory() as db3:
                result = await db3.execute(select(Device).where(Device.id == device_uuid))
                dev = result.scalar_one_or_none()
                if dev:
                    dev.status = "offline"
                    await db3.commit()
            manager.disconnect(ws)
        return

    # 设备已绑定
    conn = await manager.connect(ws, agent_id, device_uuid)
    await manager.send_json(ws, {
        "type": "welcome",
        "device_id": str(device_uuid),
        "agent_id": str(agent_id),
        "mac": device.mac,
        "firmware_version": device.firmware_version,
    })
    await manager.send_json(ws, {
        "type": "agent_switch",
        "agent_id": str(agent_id),
    })
    print(f"[device] bound device online → agent={str(agent_id)[:8]}... device={str(device_uuid)[-8:]}")
    try:
        while True:
            raw = await ws.receive()
            if raw["type"] == "websocket.disconnect":
                break
    except WebSocketDisconnect:
        pass
    finally:
        async with async_session_factory() as db3:
            result = await db3.execute(select(Device).where(Device.id == device_uuid))
            dev = result.scalar_one_or_none()
            if dev:
                dev.status = "offline"
                await db3.commit()
        manager.disconnect(ws)
