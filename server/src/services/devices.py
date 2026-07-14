import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.device import Device
from src.models.agent import Agent
from src.schemas.device import DeviceResponse
from src.ws.manager import manager


async def list_devices(db: AsyncSession, user_id: uuid.UUID) -> list[DeviceResponse]:
    result = await db.execute(
        select(Device)
        .options(selectinload(Device.agent))
        .where(Device.user_id == user_id)
        .order_by(Device.created_at.desc())
    )
    devices = result.scalars().all()
    return [_device_to_response(d) for d in devices]


async def get_device(db: AsyncSession, device_id: uuid.UUID, user_id: uuid.UUID) -> DeviceResponse | None:
    result = await db.execute(
        select(Device)
        .options(selectinload(Device.agent))
        .where(Device.id == device_id, Device.user_id == user_id)
    )
    device = result.scalar_one_or_none()
    return _device_to_response(device) if device else None


async def bind_device(db: AsyncSession, code: str, agent_id: uuid.UUID | None = None) -> DeviceResponse:
    # 用绑定码查找设备
    result = await db.execute(
        select(Device).options(selectinload(Device.agent)).where(Device.bind_code == code)
    )
    device = result.scalar_one_or_none()

    if device:
        device.bound_agent_id = agent_id
        device.bind_code = None   # 绑定后清除验证码
        device.status = "online"  # 绑定后上线
        await db.commit()
        await db.refresh(device)
        return _device_to_response(device)

    # 绑定码不匹配，返回 None（路由层返回 404）
    return None


async def unbind_device(db: AsyncSession, device_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.user_id == user_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        return False
    await db.delete(device)
    await db.commit()
    return True


async def assign_role(db: AsyncSession, device_id: uuid.UUID, agent_id: uuid.UUID | None, user_id: uuid.UUID) -> DeviceResponse | None:
    result = await db.execute(
        select(Device)
        .options(selectinload(Device.agent))
        .where(Device.id == device_id, Device.user_id == user_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        return None
    device.bound_agent_id = agent_id
    await db.commit()
    await db.refresh(device)

    # 推送 agent_switch 到已连接的设备 WebSocket
    conn = manager.get_by_device(str(device_id))
    if conn:
        await manager.send_json(conn.websocket, {
            "type": "agent_switch",
            "agent_id": str(agent_id) if agent_id else "",
        })
        print(f"[device] agent_switch → {str(agent_id)[:8]}... to device {str(device_id)[-8:]}")
    else:
        print(f"[device] WARN: device {str(device_id)[-8:]} not connected")

    return _device_to_response(device)


async def trigger_ota(db: AsyncSession, device_id: uuid.UUID, user_id: uuid.UUID) -> DeviceResponse | None:
    result = await db.execute(
        select(Device)
        .options(selectinload(Device.agent))
        .where(Device.id == device_id, Device.user_id == user_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        return None
    device.ota_status = "updating"
    await db.commit()
    await db.refresh(device)
    return _device_to_response(device)


def _device_to_response(device: Device) -> DeviceResponse:
    return DeviceResponse(
        id=device.id,
        name=device.name,
        mac=device.mac,
        status=device.status,
        last_conversation=device.last_conversation,
        firmware_version=device.firmware_version,
        ota_status=device.ota_status,
        auto_upgrade=device.auto_upgrade,
        bound_agent_id=device.bound_agent_id,
        bound_agent_name=device.agent.name if device.agent else None,
        bind_code=device.bind_code,
        user_id=device.user_id,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )
