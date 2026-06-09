import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src import services
from src.schemas.device import DeviceBindRequest, DeviceAssignRoleRequest
from src.schemas.common import ApiResponse
import time

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("")
async def list_devices(db: AsyncSession = Depends(get_db)):
    data = await services.devices.list_devices(db)
    return ApiResponse(data=data, timestamp=time.time())


@router.get("/{device_id}")
async def get_device(device_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    device = await services.devices.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return ApiResponse(data=device, timestamp=time.time())


@router.post("/bind", status_code=201)
async def bind_device(body: DeviceBindRequest, db: AsyncSession = Depends(get_db)):
    device = await services.devices.bind_device(db, body.code, body.agentId)
    return ApiResponse(data=device, timestamp=time.time())


@router.delete("/{device_id}/unbind")
async def unbind_device(device_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    ok = await services.devices.unbind_device(db, device_id)
    if not ok:
        raise HTTPException(status_code=404, detail="设备不存在")
    return ApiResponse(data=None, timestamp=time.time())


@router.put("/{device_id}/role")
async def assign_role(device_id: uuid.UUID, body: DeviceAssignRoleRequest, db: AsyncSession = Depends(get_db)):
    device = await services.devices.assign_role(db, device_id, body.agent_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return ApiResponse(data=device, timestamp=time.time())


@router.post("/{device_id}/upgrade")
async def trigger_upgrade(device_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    device = await services.devices.trigger_ota(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return ApiResponse(data=device, timestamp=time.time())
