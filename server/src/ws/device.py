import json
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.ws.manager import manager
from src.database import async_session_factory
from src.models.device import Device


async def handle_device(ws: WebSocket, device_id: str):
    import uuid as uuid_mod
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
            # 自动注册（pending 状态，绑定码等 firmware 上报）
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
        # 设备未绑定角色：等 firmware 上报 device_info（含绑定码）后再发 welcome
        conn = await manager.connect(ws, None, device_uuid)

        # 等第一条 device_info
        try:
            while True:
                raw = await ws.receive()
                if raw["type"] == "websocket.disconnect":
                    return
                if "text" in raw:
                    try:
                        msg = json.loads(raw["text"])
                        if msg.get("type") == "device_info" and msg.get("bind_code"):
                            async with async_session_factory() as db2:
                                result = await db2.execute(select(Device).where(Device.id == device_uuid))
                                dev = result.scalar_one_or_none()
                                if dev:
                                    dev.bind_code = msg["bind_code"]
                                    await db2.commit()
                            # 拿到真实绑定码后发送 welcome
                            await manager.send_json(ws, {
                                "type": "welcome",
                                "device_id": str(device_uuid),
                                "agent_id": None,
                                "bind_code": msg["bind_code"],
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

        # 已拿到绑定码，wait_for 保持连接
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

    # 设备已绑定，仅保持管理连接（在线状态 + 接收 agent_switch）
    conn = await manager.connect(ws, agent_id, device_uuid)
    await manager.send_json(ws, {
        "type": "welcome",
        "device_id": str(device_uuid),
        "agent_id": str(agent_id),
        "mac": device.mac,
        "firmware_version": device.firmware_version,
    })
    # 已绑定的设备上线时，主动推送 agent_switch 让板子重连正确的语音通道
    await manager.send_json(ws, {
        "type": "agent_switch",
        "agent_id": str(agent_id),
    })
    print(f"[device] bound device online, pushed agent_switch → {str(agent_id)[:8]}... to {str(device_uuid)[-8:]}")
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
