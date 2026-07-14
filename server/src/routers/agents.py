import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src import services
from src.models.user import User
from src.dependencies import get_current_user
from src.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from src.schemas.common import ApiResponse
import time

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("")
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await services.agents.list_agents(db, current_user.id)
    return ApiResponse(data=data, timestamp=time.time())


@router.get("/{agent_id}")
async def get_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = await services.agents.get_agent(db, agent_id, current_user.id)
    if not agent:
        raise HTTPException(status_code=404, detail="角色不存在")
    return ApiResponse(data=agent, timestamp=time.time())


@router.post("", status_code=201)
async def create_agent(
    body: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = await services.agents.create_agent(db, body, current_user.id)
    return ApiResponse(data=agent, timestamp=time.time())


@router.put("/{agent_id}")
async def update_agent(
    agent_id: uuid.UUID,
    body: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = await services.agents.update_agent(db, agent_id, body, current_user.id)
    if not agent:
        raise HTTPException(status_code=404, detail="角色不存在")
    return ApiResponse(data=agent, timestamp=time.time())


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = await services.agents.delete_agent(db, agent_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="角色不存在")
    return ApiResponse(data=None, timestamp=time.time())
