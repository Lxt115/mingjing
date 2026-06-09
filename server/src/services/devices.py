import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.device import Device
from src.models.agent import Agent
from src.schemas.device import DeviceResponse


async def list_devices(db: AsyncSession) -> list[DeviceResponse]:
    result = await db.execute(
        select(Device).options(selectinload(Device.agent)).order_by(Device.created_at.desc())
    )
    devices = result.scalars().all()
    return [_device_to_response(d) for d in devices]


async def get_device(db: AsyncSession, device_id: uuid.UUID) -> DeviceResponse | None:
    result = await db.execute(
        select(Device).options(selectinload(Device.agent)).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()
    return _device_to_response(device) if device else None


async def bind_device(db: AsyncSession, mac: str, agent_id: uuid.UUID | None = None) -> DeviceResponse:
    existing = await db.execute(select(Device).where(Device.mac == mac))
    device = existing.scalar_one_or_none()

    if device:
        device.bound_agent_id = agent_id
    else:
        device = Device(
            name=f"设备-{mac[-4:]}",
            mac=mac,
            status="online",
            bound_agent_id=agent_id,
        )
        db.add(device)

    await db.commit()
    await db.refresh(device)

    result = await db.execute(
        select(Device).options(selectinload(Device.agent)).where(Device.id == device.id)
    )
    return _device_to_response(result.scalar_one())


async def unbind_device(db: AsyncSession, device_id: uuid.UUID) -> bool:
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        return False
    await db.delete(device)
    await db.commit()
    return True


async def assign_role(db: AsyncSession, device_id: uuid.UUID, agent_id: uuid.UUID | None) -> DeviceResponse | None:
    result = await db.execute(select(Device).options(selectinload(Device.agent)).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        return None
    device.bound_agent_id = agent_id
    await db.commit()
    await db.refresh(device)
    return _device_to_response(device)


async def trigger_ota(db: AsyncSession, device_id: uuid.UUID) -> DeviceResponse | None:
    result = await db.execute(select(Device).options(selectinload(Device.agent)).where(Device.id == device_id))
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
        created_at=device.created_at,
        updated_at=device.updated_at,
    )
