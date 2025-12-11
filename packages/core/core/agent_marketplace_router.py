"""Agent marketplace API routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlmodel import Session
from .logger import logger
from .agent_marketplace_models import (
    AgentResponse,
    OrganizationAgentResponse,
    AgentConfigUpdate,
    AgentDeployRequest,
    AgentEnableRequest,
)
from .agent_marketplace_service import AgentMarketplaceService
from .database import get_session
from .dependencies import get_current_active_user, get_user_org_id
from .models import User

router = APIRouter()


def get_marketplace_service() -> AgentMarketplaceService:
    """Get marketplace service instance."""
    return AgentMarketplaceService()


@router.get("/agents", response_model=List[AgentResponse])
async def list_agents(
    category: Optional[str] = None,
    is_active: bool = True,
    service: AgentMarketplaceService = Depends(get_marketplace_service),
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    """List all available agents in the marketplace."""
    try:
        agents = service.list_agents(session, category=category, is_active=is_active)
        return [AgentResponse.model_validate(agent) for agent in agents]
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    service: AgentMarketplaceService = Depends(get_marketplace_service),
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    """Get agent details by ID."""
    try:
        agent = service.get_agent(session, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return AgentResponse.model_validate(agent)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/organization/agents", response_model=List[OrganizationAgentResponse])
async def list_organization_agents(
    service: AgentMarketplaceService = Depends(get_marketplace_service),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    org_id: str = Depends(get_user_org_id),
):
    """List agents deployed for the current organization."""
    try:
        if not org_id:
            raise HTTPException(status_code=400, detail="Organization ID required")

        org_agents = service.list_organization_agents(session, org_id)
        result = []
        for org_agent in org_agents:
            agent = service.get_agent(session, org_agent.agent_id)
            response = OrganizationAgentResponse.model_validate(org_agent)
            if agent:
                response.agent = AgentResponse.model_validate(agent)
            result.append(response)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing organization agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/organization/agents/{agent_id}", response_model=OrganizationAgentResponse)
async def get_organization_agent(
    agent_id: str,
    service: AgentMarketplaceService = Depends(get_marketplace_service),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    org_id: str = Depends(get_user_org_id),
):
    """Get organization agent deployment details."""
    try:
        if not org_id:
            raise HTTPException(status_code=400, detail="Organization ID required")

        org_agent = service.get_organization_agent(session, org_id, agent_id)
        if not org_agent:
            raise HTTPException(
                status_code=404, detail="Agent not deployed for this organization"
            )

        agent = service.get_agent(session, agent_id)
        response = OrganizationAgentResponse.model_validate(org_agent)
        if agent:
            response.agent = AgentResponse.model_validate(agent)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/organization/agents/{agent_id}/deploy", response_model=OrganizationAgentResponse)
async def deploy_agent(
    agent_id: str,
    deploy_request: AgentDeployRequest,
    service: AgentMarketplaceService = Depends(get_marketplace_service),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    org_id: str = Depends(get_user_org_id),
):
    """Deploy an agent for the organization."""
    try:
        if not org_id:
            raise HTTPException(status_code=400, detail="Organization ID required")

        org_agent = service.deploy_agent(
            session=session,
            org_id=org_id,
            agent_id=agent_id,
            config=deploy_request.config,
            deployed_by=current_user.id,
            enable_tasks=deploy_request.enable_tasks,
            enable_tools=deploy_request.enable_tools,
        )

        agent = service.get_agent(session, agent_id)
        response = OrganizationAgentResponse.model_validate(org_agent)
        if agent:
            response.agent = AgentResponse.model_validate(agent)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deploying agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/organization/agents/{agent_id}/config", response_model=OrganizationAgentResponse)
async def update_agent_config(
    agent_id: str,
    config_update: AgentConfigUpdate,
    service: AgentMarketplaceService = Depends(get_marketplace_service),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    org_id: str = Depends(get_user_org_id),
):
    """Update agent configuration."""
    try:
        if not org_id:
            raise HTTPException(status_code=400, detail="Organization ID required")

        org_agent = service.update_agent_config(
            session=session,
            org_id=org_id,
            agent_id=agent_id,
            config=config_update.config,
        )

        agent = service.get_agent(session, agent_id)
        response = OrganizationAgentResponse.model_validate(org_agent)
        if agent:
            response.agent = AgentResponse.model_validate(agent)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating agent config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/organization/agents/{agent_id}/enable", response_model=OrganizationAgentResponse)
async def enable_agent(
    agent_id: str,
    service: AgentMarketplaceService = Depends(get_marketplace_service),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    org_id: str = Depends(get_user_org_id),
):
    """Enable an agent for the organization."""
    try:
        if not org_id:
            raise HTTPException(status_code=400, detail="Organization ID required")

        org_agent = service.enable_agent(session=session, org_id=org_id, agent_id=agent_id)

        agent = service.get_agent(session, agent_id)
        response = OrganizationAgentResponse.model_validate(org_agent)
        if agent:
            response.agent = AgentResponse.model_validate(agent)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error enabling agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/organization/agents/{agent_id}/disable", response_model=OrganizationAgentResponse)
async def disable_agent(
    agent_id: str,
    service: AgentMarketplaceService = Depends(get_marketplace_service),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    org_id: str = Depends(get_user_org_id),
):
    """Disable an agent for the organization."""
    try:
        if not org_id:
            raise HTTPException(status_code=400, detail="Organization ID required")

        org_agent = service.disable_agent(session=session, org_id=org_id, agent_id=agent_id)

        agent = service.get_agent(session, agent_id)
        response = OrganizationAgentResponse.model_validate(org_agent)
        if agent:
            response.agent = AgentResponse.model_validate(agent)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error disabling agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))
