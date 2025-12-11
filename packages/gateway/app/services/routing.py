"""Agent routing service."""

import httpx
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from core.logger import logger
from ..config import get_settings, get_agent_urls


class RoutingService:
    """Service for routing requests to agent services."""

    def __init__(self):
        self.settings = get_settings()
        self.agent_urls = get_agent_urls()
        self.client = httpx.AsyncClient(timeout=self.settings.request_timeout)

    def _get_agent_from_path(self, path: str) -> Optional[str]:
        """Extract agent name from request path."""
        # Path format: /api/{agent}/...
        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "api":
            agent = parts[1]
            if agent in self.agent_urls:
                return agent
        return None

    def _build_agent_url(self, agent: str, path: str) -> str:
        """Build full URL for agent service."""
        base_url = self.agent_urls[agent]
        # Remove /api/{agent} prefix and add to base URL
        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "api":
            agent_path = "/" + "/".join(parts[2:])  # Everything after /api/{agent}
        else:
            agent_path = path
        
        # Ensure base_url doesn't end with /
        base_url = base_url.rstrip("/")
        return f"{base_url}{agent_path}"

    async def route_request(
        self, request: Request, agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Route request to appropriate agent service.
        
        Args:
            request: FastAPI request object
            agent: Optional agent name (if not provided, extracted from path)
            
        Returns:
            Response from agent service
            
        Raises:
            HTTPException: If routing fails
        """
        if not agent:
            agent = self._get_agent_from_path(str(request.url.path))
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found in path",
            )
        
        # Build agent URL
        agent_url = self._build_agent_url(agent, str(request.url.path))
        
        # Get query parameters
        query_params = dict(request.query_params)
        
        # Get request body
        body = None
        content_type = request.headers.get("content-type", "")
        
        if request.method in ["POST", "PUT", "PATCH"]:
            if "application/json" in content_type:
                try:
                    body = await request.json()
                except Exception:
                    body = await request.body()
            elif "multipart/form-data" in content_type:
                # For file uploads, read as bytes and forward
                body = await request.body()
            else:
                body = await request.body()
        
        # Prepare headers (forward relevant headers, exclude host and content-length)
        headers = {}
        for key, value in request.headers.items():
            key_lower = key.lower()
            if key_lower not in ["host", "content-length"]:
                headers[key] = value
        
        try:
            # Make request to agent service
            logger.info(f"Routing {request.method} {request.url.path} to {agent_url}")
            
            # Handle different body types
            if isinstance(body, dict):
                response = await self.client.request(
                    method=request.method,
                    url=agent_url,
                    headers=headers,
                    params=query_params,
                    json=body,
                )
            elif body and isinstance(body, bytes):
                # For binary data (including form data), forward as content
                response = await self.client.request(
                    method=request.method,
                    url=agent_url,
                    headers=headers,
                    params=query_params,
                    content=body,
                )
            else:
                response = await self.client.request(
                    method=request.method,
                    url=agent_url,
                    headers=headers,
                    params=query_params,
                )
            
            # Parse response body
            response_body = None
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    response_body = response.json()
                except Exception:
                    response_body = response.text
            else:
                response_body = response.text
            
            # Return response
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response_body,
            }
            
        except httpx.TimeoutException:
            logger.error(f"Timeout routing request to {agent_url}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Agent service timeout",
            )
        except httpx.RequestError as e:
            logger.error(f"Error routing request to {agent_url}: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error connecting to agent service: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Unexpected error routing request: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal routing error: {str(e)}",
            )

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Global routing service instance
_routing_service: Optional[RoutingService] = None


def get_routing_service() -> RoutingService:
    """Get global routing service instance."""
    global _routing_service
    if _routing_service is None:
        _routing_service = RoutingService()
    return _routing_service
