"""Slack integration connector."""

import httpx
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode
from loguru import logger
from core.tools import ToolRegistry
from core.config import get_settings
from .base import BaseConnector


class SlackConnector(BaseConnector):
    """Slack integration connector with OAuth and tools."""

    def __init__(self, user_id: str, org_id: Optional[str] = None):
        super().__init__("slack", user_id, org_id)
        self.settings = get_settings()

    def get_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Generate Slack OAuth authorization URL."""
        client_id = get_settings().slack_client_id
        scopes = [
            "channels:read",
            "channels:history",
            "chat:write",
            "users:read",
            "files:read",
        ]
        params = {
            "client_id": client_id,
            "scope": ",".join(scopes),
            "redirect_uri": redirect_uri,
            "response_type": "code",
        }
        if state:
            params["state"] = state

        return f"https://slack.com/oauth/v2/authorize?{urlencode(params)}"

    async def handle_oauth_callback(
        self, code: str, redirect_uri: str
    ) -> Dict[str, Any]:
        """Handle Slack OAuth callback."""
        client_id = get_settings().slack_client_id
        client_secret = get_settings().slack_client_secret

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/oauth.v2.access",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )
            data = response.json()

            if not data.get("ok"):
                raise Exception(f"Slack OAuth error: {data.get('error')}")

            token_data = data.get("authed_user", {}).get("access_token")
            team_id = data.get("team", {}).get("id")

            self.store_tokens(
                token=token_data,
                metadata={"team_id": team_id, "team_name": data.get("team", {}).get("name")},
            )

            return {
                "access_token": token_data,
                "team_id": team_id,
                "team_name": data.get("team", {}).get("name"),
            }

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Slack API requests."""
        token = self.get_token()
        if not token:
            raise Exception("Not authenticated with Slack")
        return {"Authorization": f"Bearer {token}"}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of Slack tools."""
        return [
            {
                "name": "slack_send_message",
                "description": "Send a message to a Slack channel",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "channel": {"type": "string", "description": "Channel ID or name"},
                        "text": {"type": "string", "description": "Message text"},
                    },
                    "required": ["channel", "text"],
                },
            },
            {
                "name": "slack_list_channels",
                "description": "List all Slack channels",
                "parameters_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "slack_get_channel_history",
                "description": "Get message history from a Slack channel",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "channel": {"type": "string", "description": "Channel ID"},
                        "limit": {"type": "integer", "description": "Number of messages to retrieve", "default": 50},
                    },
                    "required": ["channel"],
                },
            },
            {
                "name": "slack_get_user_info",
                "description": "Get information about a Slack user",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "Slack user ID"},
                    },
                    "required": ["user_id"],
                },
            },
        ]

    def register_tools(self, registry: ToolRegistry):
        """Register Slack tools."""
        registry.register_function(
            "slack_send_message",
            "Send a message to a Slack channel",
            self._send_message,
            self.get_tools()[0]["parameters_schema"],
        )
        registry.register_function(
            "slack_list_channels",
            "List all Slack channels",
            self._list_channels,
            self.get_tools()[1]["parameters_schema"],
        )
        registry.register_function(
            "slack_get_channel_history",
            "Get message history from a Slack channel",
            self._get_channel_history,
            self.get_tools()[2]["parameters_schema"],
        )
        registry.register_function(
            "slack_get_user_info",
            "Get information about a Slack user",
            self._get_user_info,
            self.get_tools()[3]["parameters_schema"],
        )

    def _send_message(self, channel: str, text: str) -> Dict[str, Any]:
        """Send message to Slack channel."""
        try:
            with httpx.Client() as client:
                response = client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers=self._get_headers(),
                    json={"channel": channel, "text": text},
                )
                data = response.json()
                if not data.get("ok"):
                    return {"error": data.get("error"), "success": False}
                return {"success": True, "ts": data.get("ts"), "channel": data.get("channel")}
        except Exception as e:
            logger.error(f"Slack send message error: {e}")
            return {"error": str(e), "success": False}

    def _list_channels(self) -> Dict[str, Any]:
        """List Slack channels."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    "https://slack.com/api/conversations.list",
                    headers=self._get_headers(),
                    params={"types": "public_channel,private_channel"},
                )
                data = response.json()
                if not data.get("ok"):
                    return {"error": data.get("error"), "success": False}
                channels = [
                    {"id": ch["id"], "name": ch["name"], "is_private": ch.get("is_private", False)}
                    for ch in data.get("channels", [])
                ]
                return {"success": True, "channels": channels}
        except Exception as e:
            logger.error(f"Slack list channels error: {e}")
            return {"error": str(e), "success": False}

    def _get_channel_history(self, channel: str, limit: int = 50) -> Dict[str, Any]:
        """Get channel message history."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    "https://slack.com/api/conversations.history",
                    headers=self._get_headers(),
                    params={"channel": channel, "limit": limit},
                )
                data = response.json()
                if not data.get("ok"):
                    return {"error": data.get("error"), "success": False}
                messages = [
                    {
                        "text": msg.get("text"),
                        "user": msg.get("user"),
                        "ts": msg.get("ts"),
                    }
                    for msg in data.get("messages", [])
                ]
                return {"success": True, "messages": messages}
        except Exception as e:
            logger.error(f"Slack get channel history error: {e}")
            return {"error": str(e), "success": False}

    def _get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"https://slack.com/api/users.info",
                    headers=self._get_headers(),
                    params={"user": user_id},
                )
                data = response.json()
                if not data.get("ok"):
                    return {"error": data.get("error"), "success": False}
                user = data.get("user", {})
                return {
                    "success": True,
                    "user": {
                        "id": user.get("id"),
                        "name": user.get("name"),
                        "real_name": user.get("real_name"),
                        "email": user.get("profile", {}).get("email"),
                    },
                }
        except Exception as e:
            logger.error(f"Slack get user info error: {e}")
            return {"error": str(e), "success": False}
