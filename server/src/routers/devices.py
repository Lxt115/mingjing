import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import get_db
from src import services
from src.models.user import User
from src.models.agent import Agent
from src.dependencies import get_current_user
from src.schemas.device import DeviceBindRequest, DeviceAssignRoleRequest
from src.schemas.common import ApiResponse
import time

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("")
async def list_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await services.devices.list_devices(db, current_user.id)
    return ApiResponse(data=data, timestamp=time.time())


@router.get("/{device_id}")
async def get_device(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = await services.devices.get_device(db, device_id, current_user.id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return ApiResponse(data=device, timestamp=time.time())


@router.post("/bind", status_code=201)
async def bind_device(
    body: DeviceBindRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """通过配对码绑定设备。用户在设备语音播报的 4 位配对码。"""
    from src.ws.device import consume_pair_code
    device_uuid = consume_pair_code(body.code)
    if not device_uuid:
        raise HTTPException(status_code=404, detail="配对码无效或已过期")

    from src.models.device import Device
    result = await db.execute(select(Device).options(selectinload(Device.agent)).where(Device.id == device_uuid))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    device.user_id = current_user.id
    device.status = "online"
    if body.agent_id:
        device.bound_agent_id = body.agent_id
    elif not device.bound_agent_id:
        # 自动绑定用户的第一个智能体
        agent_result = await db.execute(
            select(Agent).where(Agent.user_id == current_user.id).order_by(Agent.created_at).limit(1)
        )
        first_agent = agent_result.scalar_one_or_none()
        if first_agent:
            device.bound_agent_id = first_agent.id

    await db.commit()
    await db.refresh(device)

    from src.services.devices import _device_to_response
    return ApiResponse(data=_device_to_response(device), timestamp=time.time())


@router.delete("/{device_id}/unbind")
async def unbind_device(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = await services.devices.unbind_device(db, device_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="设备不存在")
    return ApiResponse(data=None, timestamp=time.time())


@router.put("/{device_id}/role")
async def assign_role(
    device_id: uuid.UUID,
    body: DeviceAssignRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    print(f"[ROLE] device={str(device_id)[-8:]} agent_id={body.agent_id}", flush=True)
    device = await services.devices.assign_role(db, device_id, body.agent_id, current_user.id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return ApiResponse(data=device, timestamp=time.time())


@router.post("/{device_id}/upgrade")
async def trigger_upgrade(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = await services.devices.trigger_ota(db, device_id, current_user.id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return ApiResponse(data=device, timestamp=time.time())


@router.post("/provisioning/start")
async def start_provisioning(
    current_user: User = Depends(get_current_user),
):
    """开始配网（仅标记用户已进入配网页面，用于前端轮询引导）。
    实际绑定通过 POST /api/devices/bind 输入设备语音播报的配对码完成。"""
    return ApiResponse(data={
        "message": "请按照前端引导完成设备 WiFi 配置，设备会语音播报 4 位配对码",
        "expires_in_seconds": 300,
    }, timestamp=time.time())
