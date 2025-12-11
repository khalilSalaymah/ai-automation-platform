"""Notion integration connector."""

import httpx
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode
from loguru import logger
from core.tools import ToolRegistry
from core.config import get_settings
from .base import BaseConnector


class NotionConnector(BaseConnector):
    """Notion integration connector with OAuth."""

    def __init__(self, user_id: str, org_id: Optional[str] = None):
        super().__init__("notion", user_id, org_id)
        self.settings = get_settings()

    def get_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Generate Notion OAuth authorization URL."""
        client_id = self.settings.notion_client_id
        scopes = ["read", "insert", "update"]
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "owner": "user",
        }
        if state:
            params["state"] = state

        return f"https://api.notion.com/v1/oauth/authorize?{urlencode(params)}"

    async def handle_oauth_callback(
        self, code: str, redirect_uri: str
    ) -> Dict[str, Any]:
        """Handle Notion OAuth callback."""
        client_id = self.settings.notion_client_id
        client_secret = self.settings.notion_client_secret

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.notion.com/v1/oauth/token",
                auth=(client_id, client_secret),
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )
            data = response.json()

            if "error" in data:
                raise Exception(f"Notion OAuth error: {data.get('error')}")

            access_token = data.get("access_token")
            bot_id = data.get("bot_id")
            workspace_id = data.get("workspace_id")
            workspace_name = data.get("workspace_name")

            self.store_tokens(
                token=access_token,
                metadata={
                    "bot_id": bot_id,
                    "workspace_id": workspace_id,
                    "workspace_name": workspace_name,
                },
            )

            return {
                "access_token": access_token,
                "bot_id": bot_id,
                "workspace_id": workspace_id,
                "workspace_name": workspace_name,
            }

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Notion API requests."""
        token = self.get_token()
        if not token:
            raise Exception("Not authenticated with Notion")
        return {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of Notion tools."""
        return [
            {
                "name": "notion_search_pages",
                "description": "Search for pages in Notion",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "filter": {"type": "object", "description": "Filter object"},
                    },
                    "required": [],
                },
            },
            {
                "name": "notion_get_page",
                "description": "Get a specific Notion page by ID",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "page_id": {"type": "string", "description": "Notion page ID"},
                    },
                    "required": ["page_id"],
                },
            },
            {
                "name": "notion_create_page",
                "description": "Create a new page in Notion",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "parent_id": {"type": "string", "description": "Parent page or database ID"},
                        "title": {"type": "string", "description": "Page title"},
                        "properties": {"type": "object", "description": "Page properties"},
                    },
                    "required": ["parent_id", "title"],
                },
            },
            {
                "name": "notion_update_page",
                "description": "Update a Notion page",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "page_id": {"type": "string", "description": "Notion page ID"},
                        "properties": {"type": "object", "description": "Properties to update"},
                    },
                    "required": ["page_id", "properties"],
                },
            },
            {
                "name": "notion_get_databases",
                "description": "List all accessible Notion databases",
                "parameters_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        ]

    def register_tools(self, registry: ToolRegistry):
        """Register Notion tools."""
        for tool_def in self.get_tools():
            name = tool_def["name"]
            if name == "notion_search_pages":
                registry.register_function(
                    name, tool_def["description"], self._search_pages, tool_def["parameters_schema"]
                )
            elif name == "notion_get_page":
                registry.register_function(
                    name, tool_def["description"], self._get_page, tool_def["parameters_schema"]
                )
            elif name == "notion_create_page":
                registry.register_function(
                    name, tool_def["description"], self._create_page, tool_def["parameters_schema"]
                )
            elif name == "notion_update_page":
                registry.register_function(
                    name, tool_def["description"], self._update_page, tool_def["parameters_schema"]
                )
            elif name == "notion_get_databases":
                registry.register_function(
                    name, tool_def["description"], self._get_databases, tool_def["parameters_schema"]
                )

    def _search_pages(self, query: str = "", filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search Notion pages."""
        try:
            payload = {}
            if query:
                payload["query"] = query
            if filter:
                payload["filter"] = filter

            with httpx.Client() as client:
                response = client.post(
                    "https://api.notion.com/v1/search",
                    headers=self._get_headers(),
                    json=payload,
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                results = [
                    {
                        "id": result.get("id"),
                        "title": self._extract_title(result),
                        "url": result.get("url"),
                        "object": result.get("object"),
                    }
                    for result in data.get("results", [])
                ]
                return {"success": True, "results": results}
        except Exception as e:
            logger.error(f"Notion search pages error: {e}")
            return {"error": str(e), "success": False}

    def _get_page(self, page_id: str) -> Dict[str, Any]:
        """Get specific Notion page."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"https://api.notion.com/v1/pages/{page_id}",
                    headers=self._get_headers(),
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                return {
                    "success": True,
                    "id": data.get("id"),
                    "title": self._extract_title(data),
                    "url": data.get("url"),
                    "properties": data.get("properties", {}),
                }
        except Exception as e:
            logger.error(f"Notion get page error: {e}")
            return {"error": str(e), "success": False}

    def _create_page(
        self, parent_id: str, title: str, properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create Notion page."""
        try:
            payload = {
                "parent": {"page_id": parent_id},
                "properties": {
                    "title": {
                        "title": [{"text": {"content": title}}],
                    },
                },
            }

            if properties:
                payload["properties"].update(properties)

            with httpx.Client() as client:
                response = client.post(
                    "https://api.notion.com/v1/pages",
                    headers=self._get_headers(),
                    json=payload,
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                return {
                    "success": True,
                    "id": data.get("id"),
                    "url": data.get("url"),
                }
        except Exception as e:
            logger.error(f"Notion create page error: {e}")
            return {"error": str(e), "success": False}

    def _update_page(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update Notion page."""
        try:
            with httpx.Client() as client:
                response = client.patch(
                    f"https://api.notion.com/v1/pages/{page_id}",
                    headers=self._get_headers(),
                    json={"properties": properties},
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                return {"success": True, "id": data.get("id")}
        except Exception as e:
            logger.error(f"Notion update page error: {e}")
            return {"error": str(e), "success": False}

    def _get_databases(self) -> Dict[str, Any]:
        """Get Notion databases."""
        try:
            with httpx.Client() as client:
                response = client.post(
                    "https://api.notion.com/v1/search",
                    headers=self._get_headers(),
                    json={"filter": {"property": "object", "value": "database"}},
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                databases = [
                    {
                        "id": db.get("id"),
                        "title": self._extract_title(db),
                        "url": db.get("url"),
                    }
                    for db in data.get("results", [])
                ]
                return {"success": True, "databases": databases}
        except Exception as e:
            logger.error(f"Notion get databases error: {e}")
            return {"error": str(e), "success": False}

    def _extract_title(self, page_data: Dict[str, Any]) -> str:
        """Extract title from Notion page data."""
        props = page_data.get("properties", {})
        for prop_name, prop_data in props.items():
            if prop_data.get("type") == "title":
                title_parts = prop_data.get("title", [])
                if title_parts:
                    return "".join(part.get("plain_text", "") for part in title_parts)
        return "Untitled"
