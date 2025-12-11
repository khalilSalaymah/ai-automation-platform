"""Gateway API routes."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from core.logger import logger
from ..services.routing import get_routing_service, RoutingService
from ..middleware.auth import get_current_user_token
from ..middleware.quota import check_quota_middleware
from core.billing_service import BillingService
from core.billing_models import UsageType
from core.database import get_session
from sqlmodel import Session

router = APIRouter()


@router.api_route("/api/{agent:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def route_to_agent(
    request: Request,
    agent: str,
    routing_service: RoutingService = Depends(get_routing_service),
    token_data = Depends(get_current_user_token),
    session: Session = Depends(get_session),
):
    """
    Route request to appropriate agent service.
    This is a catch-all route that forwards requests to agent services.
    """
    try:
        # Route request
        response_data = await routing_service.route_request(request, agent=agent)
        
        # Record API call usage
        if token_data:
            try:
                BillingService.record_usage(
                    session=session,
                    user_id=token_data.user_id,
                    usage_type=UsageType.API_CALLS,
                    quantity=1,
                    metadata={
                        "agent": agent,
                        "method": request.method,
                        "path": str(request.url.path),
                    },
                )
            except Exception as e:
                logger.error(f"Error recording usage: {e}")
        
        # Return response with appropriate content type
        response_headers = response_data.get("headers", {})
        content_type = response_headers.get("content-type", "application/json")
        
        # Remove headers that shouldn't be forwarded
        filtered_headers = {
            k: v for k, v in response_headers.items()
            if k.lower() not in ["content-length", "transfer-encoding", "connection"]
        }
        
        if "application/json" in content_type:
            return JSONResponse(
                content=response_data["body"],
                status_code=response_data["status_code"],
                headers=filtered_headers,
            )
        else:
            from fastapi.responses import Response
            return Response(
                content=str(response_data["body"]),
                status_code=response_data["status_code"],
                headers=filtered_headers,
                media_type=content_type,
            )
    except Exception as e:
        logger.error(f"Error in gateway route: {e}")
        raise


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "gateway"}
