"""Outlook integration connector with OAuth."""

import httpx
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode
from datetime import datetime, timedelta
from loguru import logger
from core.tools import ToolRegistry
from core.config import get_settings
from .base import BaseConnector


class OutlookConnector(BaseConnector):
    """Outlook/Microsoft 365 integration connector with OAuth."""

    def __init__(self, user_id: str, org_id: Optional[str] = None):
        super().__init__("outlook", user_id, org_id)
        self.settings = get_settings()

    def get_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Generate Outlook OAuth authorization URL."""
        client_id = self.settings.microsoft_client_id
        scopes = [
            "https://graph.microsoft.com/Mail.Read",
            "https://graph.microsoft.com/Mail.Send",
            "https://graph.microsoft.com/Mail.ReadWrite",
        ]
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "response_type": "code",
            "response_mode": "query",
        }
        if state:
            params["state"] = state

        return f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urlencode(params)}"

    async def handle_oauth_callback(
        self, code: str, redirect_uri: str
    ) -> Dict[str, Any]:
        """Handle Outlook OAuth callback."""
        client_id = self.settings.microsoft_client_id
        client_secret = self.settings.microsoft_client_secret

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            data = response.json()

            if "error" in data:
                raise Exception(f"Outlook OAuth error: {data.get('error')}")

            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")
            expires_in = data.get("expires_in", 3600)
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            self.store_tokens(
                token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at.isoformat(),
            }

    def refresh_access_token(self) -> bool:
        """Refresh Outlook access token."""
        if not self._refresh_token:
            if not self.load_tokens():
                return False

        client_id = self.settings.microsoft_client_id
        client_secret = self.settings.microsoft_client_secret

        try:
            with httpx.Client() as client:
                response = client.post(
                    "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "refresh_token": self._refresh_token,
                        "grant_type": "refresh_token",
                    },
                )
                data = response.json()

                if "error" in data:
                    logger.error(f"Outlook token refresh error: {data.get('error')}")
                    return False

                access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

                self.store_tokens(
                    token=access_token,
                    refresh_token=self._refresh_token,
                    expires_at=expires_at,
                )

                return True
        except Exception as e:
            logger.error(f"Outlook token refresh failed: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Outlook API requests."""
        token = self.get_token()
        if not token:
            raise Exception("Not authenticated with Outlook")
        return {"Authorization": f"Bearer {token}"}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of Outlook tools."""
        return [
            {
                "name": "outlook_list_messages",
                "description": "List emails from Outlook inbox",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "filter": {"type": "string", "description": "OData filter query"},
                        "top": {"type": "integer", "description": "Number of results", "default": 10},
                    },
                    "required": [],
                },
            },
            {
                "name": "outlook_get_message",
                "description": "Get a specific email message by ID",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "message_id": {"type": "string", "description": "Outlook message ID"},
                    },
                    "required": ["message_id"],
                },
            },
            {
                "name": "outlook_send_message",
                "description": "Send an email via Outlook",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "array", "items": {"type": "string"}, "description": "Recipient email addresses"},
                        "subject": {"type": "string", "description": "Email subject"},
                        "body": {"type": "string", "description": "Email body (HTML)"},
                        "cc": {"type": "array", "items": {"type": "string"}, "description": "CC email addresses"},
                    },
                    "required": ["to", "subject", "body"],
                },
            },
            {
                "name": "outlook_mark_read",
                "description": "Mark an email as read",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "message_id": {"type": "string", "description": "Outlook message ID"},
                    },
                    "required": ["message_id"],
                },
            },
        ]

    def register_tools(self, registry: ToolRegistry):
        """Register Outlook tools."""
        for tool_def in self.get_tools():
            if tool_def["name"] == "outlook_list_messages":
                registry.register_function(
                    tool_def["name"],
                    tool_def["description"],
                    self._list_messages,
                    tool_def["parameters_schema"],
                )
            elif tool_def["name"] == "outlook_get_message":
                registry.register_function(
                    tool_def["name"],
                    tool_def["description"],
                    self._get_message,
                    tool_def["parameters_schema"],
                )
            elif tool_def["name"] == "outlook_send_message":
                registry.register_function(
                    tool_def["name"],
                    tool_def["description"],
                    self._send_message,
                    tool_def["parameters_schema"],
                )
            elif tool_def["name"] == "outlook_mark_read":
                registry.register_function(
                    tool_def["name"],
                    tool_def["description"],
                    self._mark_read,
                    tool_def["parameters_schema"],
                )

    def _list_messages(self, filter: str = "", top: int = 10) -> Dict[str, Any]:
        """List Outlook messages."""
        try:
            with httpx.Client() as client:
                params = {"$top": top, "$orderby": "receivedDateTime desc"}
                if filter:
                    params["$filter"] = filter

                response = client.get(
                    "https://graph.microsoft.com/v1.0/me/messages",
                    headers=self._get_headers(),
                    params=params,
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                messages = [
                    {
                        "id": msg.get("id"),
                        "subject": msg.get("subject"),
                        "from": msg.get("from", {}).get("emailAddress", {}).get("address"),
                        "receivedDateTime": msg.get("receivedDateTime"),
                        "isRead": msg.get("isRead"),
                    }
                    for msg in data.get("value", [])
                ]
                return {"success": True, "messages": messages}
        except Exception as e:
            logger.error(f"Outlook list messages error: {e}")
            return {"error": str(e), "success": False}

    def _get_message(self, message_id: str) -> Dict[str, Any]:
        """Get specific Outlook message."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"https://graph.microsoft.com/v1.0/me/messages/{message_id}",
                    headers=self._get_headers(),
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                return {
                    "success": True,
                    "id": data.get("id"),
                    "subject": data.get("subject"),
                    "from": data.get("from", {}).get("emailAddress", {}).get("address"),
                    "to": [addr.get("emailAddress", {}).get("address") for addr in data.get("toRecipients", [])],
                    "body": data.get("body", {}).get("content"),
                    "receivedDateTime": data.get("receivedDateTime"),
                    "isRead": data.get("isRead"),
                }
        except Exception as e:
            logger.error(f"Outlook get message error: {e}")
            return {"error": str(e), "success": False}

    def _send_message(
        self, to: List[str], subject: str, body: str, cc: List[str] = None
    ) -> Dict[str, Any]:
        """Send Outlook message."""
        try:
            payload = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML",
                        "content": body,
                    },
                    "toRecipients": [{"emailAddress": {"address": addr}} for addr in to],
                },
            }

            if cc:
                payload["message"]["ccRecipients"] = [{"emailAddress": {"address": addr}} for addr in cc]

            with httpx.Client() as client:
                response = client.post(
                    "https://graph.microsoft.com/v1.0/me/sendMail",
                    headers={**self._get_headers(), "Content-Type": "application/json"},
                    json=payload,
                )

                if response.status_code == 202:
                    return {"success": True}
                else:
                    data = response.json()
                    return {"error": data.get("error", {}).get("message"), "success": False}
        except Exception as e:
            logger.error(f"Outlook send message error: {e}")
            return {"error": str(e), "success": False}

    def _mark_read(self, message_id: str) -> Dict[str, Any]:
        """Mark Outlook message as read."""
        try:
            with httpx.Client() as client:
                response = client.patch(
                    f"https://graph.microsoft.com/v1.0/me/messages/{message_id}",
                    headers={**self._get_headers(), "Content-Type": "application/json"},
                    json={"isRead": True},
                )

                if response.status_code == 200:
                    return {"success": True}
                else:
                    data = response.json()
                    return {"error": data.get("error", {}).get("message"), "success": False}
        except Exception as e:
            logger.error(f"Outlook mark read error: {e}")
            return {"error": str(e), "success": False}
