import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.agent import Agent
from src.models.device import Device
from src.models.knowledge import KnowledgeBase
from src.schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentTagSchema


async def list_agents(db: AsyncSession, user_id: uuid.UUID) -> list[AgentResponse]:
    result = await db.execute(
        select(Agent)
        .options(selectinload(Agent.devices), selectinload(Agent.knowledges))
        .where(Agent.user_id == user_id)
        .order_by(Agent.created_at.desc())
    )
    agents = result.scalars().all()
    return [_agent_to_response(a) for a in agents]


async def get_agent(db: AsyncSession, agent_id: uuid.UUID, user_id: uuid.UUID) -> AgentResponse | None:
    result = await db.execute(
        select(Agent)
        .options(selectinload(Agent.devices), selectinload(Agent.knowledges))
        .where(Agent.id == agent_id, Agent.user_id == user_id)
    )
    agent = result.scalar_one_or_none()
    return _agent_to_response(agent) if agent else None


async def create_agent(db: AsyncSession, data: AgentCreate, user_id: uuid.UUID) -> AgentResponse:
    agent = Agent(
        name=data.name,
        emoji=data.emoji,
        description=data.description,
        system_prompt=data.system_prompt,
        voice_id=data.voice_id,
        tags=[t.model_dump() for t in data.tags],
        user_id=user_id,
    )
    if data.knowledge_ids:
        kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id.in_(data.knowledge_ids)))
        agent.knowledges = kb_result.scalars().all()

    if data.device_ids:
        dev_result = await db.execute(select(Device).where(Device.id.in_(data.device_ids), Device.user_id == user_id))
        for dev in dev_result.scalars().all():
            dev.bound_agent_id = agent.id

    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    result = await db.execute(
        select(Agent).options(selectinload(Agent.devices), selectinload(Agent.knowledges)).where(Agent.id == agent.id)
    )
    return _agent_to_response(result.scalar_one())


async def update_agent(db: AsyncSession, agent_id: uuid.UUID, data: AgentUpdate, user_id: uuid.UUID) -> AgentResponse | None:
    result = await db.execute(
        select(Agent)
        .options(selectinload(Agent.devices), selectinload(Agent.knowledges))
        .where(Agent.id == agent_id, Agent.user_id == user_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        return None

    update_data = data.model_dump(exclude_unset=True)
    knowledge_ids = update_data.pop("knowledge_ids", None)
    device_ids = update_data.pop("device_ids", None)
    tags_raw = update_data.pop("tags", None)

    for key, value in update_data.items():
        setattr(agent, key, value)

    if tags_raw is not None:
        agent.tags = [t if isinstance(t, dict) else t.model_dump() for t in tags_raw]

    if knowledge_ids is not None:
        kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id.in_(knowledge_ids)))
        agent.knowledges = kb_result.scalars().all()

    if device_ids is not None:
        old_devices = (await db.execute(select(Device).where(Device.bound_agent_id == agent_id))).scalars().all()
        for dev in old_devices:
            dev.bound_agent_id = None
        if device_ids:
            dev_result = await db.execute(select(Device).where(Device.id.in_(device_ids), Device.user_id == user_id))
            for dev in dev_result.scalars().all():
                dev.bound_agent_id = agent_id

    await db.commit()
    await db.refresh(agent)
    return _agent_to_response(agent)


async def delete_agent(db: AsyncSession, agent_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    result = await db.execute(select(Agent).where(Agent.id == agent_id, Agent.user_id == user_id))
    agent = result.scalar_one_or_none()
    if not agent:
        return False
    await db.delete(agent)
    await db.commit()
    return True


async def copy_system_agents_for_user(db: AsyncSession, user_id: uuid.UUID) -> int:
    """将系统默认智能体复制给新注册用户。返回复制的数量。"""
    result = await db.execute(
        select(Agent).options(selectinload(Agent.knowledges)).where(Agent.user_id.is_(None))
    )
    system_agents = result.scalars().all()
    count = 0
    for sa in system_agents:
        agent = Agent(
            name=sa.name,
            emoji=sa.emoji,
            style=sa.style,
            description=sa.description,
            tags=sa.tags,
            status=sa.status,
            system_prompt=sa.system_prompt,
            voice_id=sa.voice_id,
            speed=sa.speed,
            volume=sa.volume,
            pitch=sa.pitch,
            user_id=user_id,
        )
        if sa.knowledges:
            agent.knowledges = list(sa.knowledges)
        db.add(agent)
        count += 1
    await db.commit()
    return count


def _agent_to_response(agent: Agent) -> AgentResponse:
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        emoji=agent.emoji,
        style=agent.style or {},
        description=agent.description,
        tags=[AgentTagSchema(**t) for t in (agent.tags or [])],
        status=agent.status,
        system_prompt=agent.system_prompt,
        voice_id=agent.voice_id,
        knowledge_ids=[kb.id for kb in (agent.knowledges or [])],
        bound_device_ids=[d.id for d in (agent.devices or [])],
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )
