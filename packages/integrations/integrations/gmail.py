"""Gmail integration connector with OAuth."""

import httpx
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode
from datetime import datetime, timedelta
from loguru import logger
from core.tools import ToolRegistry
from core.config import get_settings
from .base import BaseConnector


class GmailConnector(BaseConnector):
    """Gmail integration connector with OAuth."""

    def __init__(self, user_id: str, org_id: Optional[str] = None):
        super().__init__("gmail", user_id, org_id)
        self.settings = get_settings()

    def get_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Generate Gmail OAuth authorization URL."""
        client_id = self.settings.google_client_id
        scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.modify",
        ]
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
        }
        if state:
            params["state"] = state

        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    async def handle_oauth_callback(
        self, code: str, redirect_uri: str
    ) -> Dict[str, Any]:
        """Handle Gmail OAuth callback."""
        client_id = self.settings.google_client_id
        client_secret = self.settings.google_client_secret

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
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
                raise Exception(f"Gmail OAuth error: {data.get('error')}")

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
        """Refresh Gmail access token."""
        if not self._refresh_token:
            if not self.load_tokens():
                return False

        client_id = self.settings.google_client_id
        client_secret = self.settings.google_client_secret

        try:
            with httpx.Client() as client:
                response = client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "refresh_token": self._refresh_token,
                        "grant_type": "refresh_token",
                    },
                )
                data = response.json()

                if "error" in data:
                    logger.error(f"Gmail token refresh error: {data.get('error')}")
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
            logger.error(f"Gmail token refresh failed: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Gmail API requests."""
        token = self.get_token()
        if not token:
            raise Exception("Not authenticated with Gmail")
        return {"Authorization": f"Bearer {token}"}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of Gmail tools."""
        return [
            {
                "name": "gmail_list_messages",
                "description": "List emails from Gmail inbox",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Gmail search query"},
                        "max_results": {"type": "integer", "description": "Maximum number of results", "default": 10},
                    },
                    "required": [],
                },
            },
            {
                "name": "gmail_get_message",
                "description": "Get a specific email message by ID",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "message_id": {"type": "string", "description": "Gmail message ID"},
                    },
                    "required": ["message_id"],
                },
            },
            {
                "name": "gmail_send_message",
                "description": "Send an email via Gmail",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email address"},
                        "subject": {"type": "string", "description": "Email subject"},
                        "body": {"type": "string", "description": "Email body (plain text or HTML)"},
                        "cc": {"type": "string", "description": "CC email addresses (comma-separated)"},
                        "bcc": {"type": "string", "description": "BCC email addresses (comma-separated)"},
                    },
                    "required": ["to", "subject", "body"],
                },
            },
            {
                "name": "gmail_mark_read",
                "description": "Mark an email as read",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "message_id": {"type": "string", "description": "Gmail message ID"},
                    },
                    "required": ["message_id"],
                },
            },
        ]

    def register_tools(self, registry: ToolRegistry):
        """Register Gmail tools."""
        for tool_def in self.get_tools():
            if tool_def["name"] == "gmail_list_messages":
                registry.register_function(
                    tool_def["name"],
                    tool_def["description"],
                    self._list_messages,
                    tool_def["parameters_schema"],
                )
            elif tool_def["name"] == "gmail_get_message":
                registry.register_function(
                    tool_def["name"],
                    tool_def["description"],
                    self._get_message,
                    tool_def["parameters_schema"],
                )
            elif tool_def["name"] == "gmail_send_message":
                registry.register_function(
                    tool_def["name"],
                    tool_def["description"],
                    self._send_message,
                    tool_def["parameters_schema"],
                )
            elif tool_def["name"] == "gmail_mark_read":
                registry.register_function(
                    tool_def["name"],
                    tool_def["description"],
                    self._mark_read,
                    tool_def["parameters_schema"],
                )

    def _list_messages(self, query: str = "", max_results: int = 10) -> Dict[str, Any]:
        """List Gmail messages."""
        try:
            with httpx.Client() as client:
                params = {"maxResults": max_results}
                if query:
                    params["q"] = query

                response = client.get(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                    headers=self._get_headers(),
                    params=params,
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                messages = data.get("messages", [])
                return {"success": True, "messages": messages, "resultSizeEstimate": data.get("resultSizeEstimate")}
        except Exception as e:
            logger.error(f"Gmail list messages error: {e}")
            return {"error": str(e), "success": False}

    def _get_message(self, message_id: str) -> Dict[str, Any]:
        """Get specific Gmail message."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
                    headers=self._get_headers(),
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                # Parse message
                payload = data.get("payload", {})
                headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

                return {
                    "success": True,
                    "id": data.get("id"),
                    "threadId": data.get("threadId"),
                    "snippet": data.get("snippet"),
                    "subject": headers.get("Subject"),
                    "from": headers.get("From"),
                    "to": headers.get("To"),
                    "date": headers.get("Date"),
                    "body": self._extract_body(payload),
                }
        except Exception as e:
            logger.error(f"Gmail get message error: {e}")
            return {"error": str(e), "success": False}

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from payload."""
        body = ""
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    if data:
                        import base64
                        body = base64.urlsafe_b64decode(data).decode("utf-8")
                        break
        elif payload.get("mimeType") == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                import base64
                body = base64.urlsafe_b64decode(data).decode("utf-8")
        return body

    def _send_message(
        self, to: str, subject: str, body: str, cc: str = "", bcc: str = ""
    ) -> Dict[str, Any]:
        """Send Gmail message."""
        try:
            import base64
            from email.mime.text import MIMEText

            msg = MIMEText(body)
            msg["To"] = to
            msg["Subject"] = subject
            if cc:
                msg["Cc"] = cc
            if bcc:
                msg["Bcc"] = bcc

            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()

            with httpx.Client() as client:
                response = client.post(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                    headers=self._get_headers(),
                    json={"raw": raw_message},
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                return {"success": True, "id": data.get("id"), "threadId": data.get("threadId")}
        except Exception as e:
            logger.error(f"Gmail send message error: {e}")
            return {"error": str(e), "success": False}

    def _mark_read(self, message_id: str) -> Dict[str, Any]:
        """Mark Gmail message as read."""
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/modify",
                    headers=self._get_headers(),
                    json={"removeLabelIds": ["UNREAD"]},
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                return {"success": True, "id": data.get("id")}
        except Exception as e:
            logger.error(f"Gmail mark read error: {e}")
            return {"error": str(e), "success": False}
