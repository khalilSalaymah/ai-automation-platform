"""Gateway client for external developers."""

import httpx
from typing import Optional, Dict, Any, Union
from .exceptions import (
    GatewayError,
    AuthenticationError,
    QuotaExceededError,
    RateLimitError,
)


class GatewayClient:
    """
    Python SDK client for AI Automation Platform Gateway.
    
    Example:
        ```python
        from gateway_sdk import GatewayClient
        
        client = GatewayClient(
            base_url="https://api.example.com",
            api_key="your-api-key"
        )
        
        # Make a request to email agent
        response = client.email.process({
            "subject": "Hello",
            "body": "World"
        })
        ```
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 30,
    ):
        """
        Initialize gateway client.
        
        Args:
            base_url: Base URL of the gateway service
            api_key: JWT API key/token
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        
        # Agent clients
        self.email = AgentClient(self.client, "email")
        self.rag = AgentClient(self.client, "rag")
        self.scraper = AgentClient(self.client, "scraper")
        self.support = AgentClient(self.client, "support")
        self.aiops = AgentClient(self.client, "aiops")

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Make a raw request to the gateway.
        
        Args:
            method: HTTP method
            path: API path
            params: Query parameters
            json: JSON body
            data: Raw body data
            
        Returns:
            Response data
            
        Raises:
            GatewayError: For gateway errors
            AuthenticationError: For authentication errors
            QuotaExceededError: For quota exceeded errors
            RateLimitError: For rate limit errors
        """
        try:
            response = self.client.request(
                method=method,
                url=path,
                params=params,
                json=json,
                content=data,
            )
            
            # Handle errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid or missing API key")
            elif response.status_code == 402:
                raise QuotaExceededError(
                    response.json().get("detail", "Quota exceeded")
                )
            elif response.status_code == 429:
                raise RateLimitError(
                    response.json().get("detail", "Rate limit exceeded")
                )
            elif response.status_code >= 400:
                raise GatewayError(
                    f"Gateway error: {response.status_code} - {response.text}"
                )
            
            # Parse response
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            else:
                return {"content": response.text}
                
        except httpx.TimeoutException:
            raise GatewayError("Request timeout")
        except httpx.RequestError as e:
            raise GatewayError(f"Request error: {str(e)}")
        except (AuthenticationError, QuotaExceededError, RateLimitError):
            raise
        except Exception as e:
            raise GatewayError(f"Unexpected error: {str(e)}")

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class AgentClient:
    """Client for a specific agent."""

    def __init__(self, client: httpx.Client, agent_name: str):
        """
        Initialize agent client.
        
        Args:
            client: HTTP client
            agent_name: Name of the agent
        """
        self.client = client
        self.agent_name = agent_name
        self.base_path = f"/api/{agent_name}"

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Make request to agent endpoint."""
        full_path = f"{self.base_path}{path}"
        
        try:
            response = self.client.request(
                method=method,
                url=full_path,
                params=params,
                json=json,
                content=data,
            )
            
            # Handle errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid or missing API key")
            elif response.status_code == 402:
                raise QuotaExceededError(
                    response.json().get("detail", "Quota exceeded")
                )
            elif response.status_code == 429:
                raise RateLimitError(
                    response.json().get("detail", "Rate limit exceeded")
                )
            elif response.status_code >= 400:
                raise GatewayError(
                    f"Agent error: {response.status_code} - {response.text}"
                )
            
            # Parse response
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            else:
                return {"content": response.text}
                
        except httpx.TimeoutException:
            raise GatewayError("Request timeout")
        except httpx.RequestError as e:
            raise GatewayError(f"Request error: {str(e)}")
        except (AuthenticationError, QuotaExceededError, RateLimitError):
            raise
        except Exception as e:
            raise GatewayError(f"Unexpected error: {str(e)}")

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request."""
        return self._request("GET", path, params=params)

    def post(
        self, path: str, json: Optional[Dict[str, Any]] = None, data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Make POST request."""
        return self._request("POST", path, json=json, data=data)

    def put(
        self, path: str, json: Optional[Dict[str, Any]] = None, data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Make PUT request."""
        return self._request("PUT", path, json=json, data=data)

    def patch(
        self, path: str, json: Optional[Dict[str, Any]] = None, data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Make PATCH request."""
        return self._request("PATCH", path, json=json, data=data)

    def delete(self, path: str) -> Dict[str, Any]:
        """Make DELETE request."""
        return self._request("DELETE", path)


# Convenience methods for common agent operations
class EmailAgentClient(AgentClient):
    """Email agent client with convenience methods."""

    def process(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process an email."""
        return self.post("/process", json=email_data)

    def respond(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate email response."""
        return self.post("/respond", json=email_data)

    def get_history(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """Get email history."""
        return self.get("/history", params={"limit": limit, "offset": offset})


class RAGAgentClient(AgentClient):
    """RAG agent client with convenience methods."""

    def chat(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Chat with RAG."""
        return self.post("/chat", json={"message": message, "session_id": session_id})

    def upload_document(self, file_path: str) -> Dict[str, Any]:
        """Upload document for indexing."""
        with open(file_path, "rb") as f:
            return self.post("/documents/upload", data=f.read())

    def list_documents(self) -> Dict[str, Any]:
        """List indexed documents."""
        return self.get("/documents")
