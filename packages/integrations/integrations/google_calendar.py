"""Google Calendar integration connector with OAuth."""

import httpx
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode
from datetime import datetime, timedelta
from loguru import logger
from core.tools import ToolRegistry
from core.config import get_settings
from .base import BaseConnector


class GoogleCalendarConnector(BaseConnector):
    """Google Calendar integration connector with OAuth."""

    def __init__(self, user_id: str, org_id: Optional[str] = None):
        super().__init__("google_calendar", user_id, org_id)
        self.settings = get_settings()

    def get_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Generate Google Calendar OAuth authorization URL."""
        client_id = self.settings.google_client_id
        scopes = [
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/calendar.events",
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
        """Handle Google Calendar OAuth callback."""
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
                raise Exception(f"Google Calendar OAuth error: {data.get('error')}")

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
        """Refresh Google Calendar access token."""
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
                    logger.error(f"Google Calendar token refresh error: {data.get('error')}")
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
            logger.error(f"Google Calendar token refresh failed: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Google Calendar API requests."""
        token = self.get_token()
        if not token:
            raise Exception("Not authenticated with Google Calendar")
        return {"Authorization": f"Bearer {token}"}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of Google Calendar tools."""
        return [
            {
                "name": "calendar_list_calendars",
                "description": "List all Google Calendars",
                "parameters_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "calendar_list_events",
                "description": "List events from a Google Calendar",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "calendar_id": {"type": "string", "description": "Calendar ID (default: primary)", "default": "primary"},
                        "time_min": {"type": "string", "description": "Minimum time (ISO 8601)"},
                        "time_max": {"type": "string", "description": "Maximum time (ISO 8601)"},
                        "max_results": {"type": "integer", "description": "Maximum number of results", "default": 10},
                    },
                    "required": [],
                },
            },
            {
                "name": "calendar_get_event",
                "description": "Get a specific event by ID",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "calendar_id": {"type": "string", "description": "Calendar ID (default: primary)", "default": "primary"},
                        "event_id": {"type": "string", "description": "Event ID"},
                    },
                    "required": ["event_id"],
                },
            },
            {
                "name": "calendar_create_event",
                "description": "Create a new calendar event",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "calendar_id": {"type": "string", "description": "Calendar ID (default: primary)", "default": "primary"},
                        "summary": {"type": "string", "description": "Event title"},
                        "description": {"type": "string", "description": "Event description"},
                        "start": {"type": "string", "description": "Start time (ISO 8601)"},
                        "end": {"type": "string", "description": "End time (ISO 8601)"},
                        "attendees": {"type": "array", "items": {"type": "string"}, "description": "Attendee email addresses"},
                    },
                    "required": ["summary", "start", "end"],
                },
            },
            {
                "name": "calendar_update_event",
                "description": "Update an existing calendar event",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "calendar_id": {"type": "string", "description": "Calendar ID (default: primary)", "default": "primary"},
                        "event_id": {"type": "string", "description": "Event ID"},
                        "summary": {"type": "string", "description": "Event title"},
                        "description": {"type": "string", "description": "Event description"},
                        "start": {"type": "string", "description": "Start time (ISO 8601)"},
                        "end": {"type": "string", "description": "End time (ISO 8601)"},
                    },
                    "required": ["event_id"],
                },
            },
            {
                "name": "calendar_delete_event",
                "description": "Delete a calendar event",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "calendar_id": {"type": "string", "description": "Calendar ID (default: primary)", "default": "primary"},
                        "event_id": {"type": "string", "description": "Event ID"},
                    },
                    "required": ["event_id"],
                },
            },
        ]

    def register_tools(self, registry: ToolRegistry):
        """Register Google Calendar tools."""
        for tool_def in self.get_tools():
            name = tool_def["name"]
            if name == "calendar_list_calendars":
                registry.register_function(
                    name, tool_def["description"], self._list_calendars, tool_def["parameters_schema"]
                )
            elif name == "calendar_list_events":
                registry.register_function(
                    name, tool_def["description"], self._list_events, tool_def["parameters_schema"]
                )
            elif name == "calendar_get_event":
                registry.register_function(
                    name, tool_def["description"], self._get_event, tool_def["parameters_schema"]
                )
            elif name == "calendar_create_event":
                registry.register_function(
                    name, tool_def["description"], self._create_event, tool_def["parameters_schema"]
                )
            elif name == "calendar_update_event":
                registry.register_function(
                    name, tool_def["description"], self._update_event, tool_def["parameters_schema"]
                )
            elif name == "calendar_delete_event":
                registry.register_function(
                    name, tool_def["description"], self._delete_event, tool_def["parameters_schema"]
                )

    def _list_calendars(self) -> Dict[str, Any]:
        """List Google Calendars."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    "https://www.googleapis.com/calendar/v3/users/me/calendarList",
                    headers=self._get_headers(),
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                calendars = [
                    {
                        "id": cal.get("id"),
                        "summary": cal.get("summary"),
                        "description": cal.get("description"),
                    }
                    for cal in data.get("items", [])
                ]
                return {"success": True, "calendars": calendars}
        except Exception as e:
            logger.error(f"Google Calendar list calendars error: {e}")
            return {"error": str(e), "success": False}

    def _list_events(
        self, calendar_id: str = "primary", time_min: str = "", time_max: str = "", max_results: int = 10
    ) -> Dict[str, Any]:
        """List calendar events."""
        try:
            params = {"maxResults": max_results}
            if time_min:
                params["timeMin"] = time_min
            if time_max:
                params["timeMax"] = time_max

            with httpx.Client() as client:
                response = client.get(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                    headers=self._get_headers(),
                    params=params,
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                events = [
                    {
                        "id": event.get("id"),
                        "summary": event.get("summary"),
                        "start": event.get("start", {}).get("dateTime") or event.get("start", {}).get("date"),
                        "end": event.get("end", {}).get("dateTime") or event.get("end", {}).get("date"),
                    }
                    for event in data.get("items", [])
                ]
                return {"success": True, "events": events}
        except Exception as e:
            logger.error(f"Google Calendar list events error: {e}")
            return {"error": str(e), "success": False}

    def _get_event(self, event_id: str, calendar_id: str = "primary") -> Dict[str, Any]:
        """Get specific calendar event."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}",
                    headers=self._get_headers(),
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                return {
                    "success": True,
                    "id": data.get("id"),
                    "summary": data.get("summary"),
                    "description": data.get("description"),
                    "start": data.get("start", {}).get("dateTime") or data.get("start", {}).get("date"),
                    "end": data.get("end", {}).get("dateTime") or data.get("end", {}).get("date"),
                    "attendees": [a.get("email") for a in data.get("attendees", [])],
                }
        except Exception as e:
            logger.error(f"Google Calendar get event error: {e}")
            return {"error": str(e), "success": False}

    def _create_event(
        self,
        summary: str,
        start: str,
        end: str,
        calendar_id: str = "primary",
        description: str = "",
        attendees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create calendar event."""
        try:
            payload = {
                "summary": summary,
                "start": {"dateTime": start, "timeZone": "UTC"},
                "end": {"dateTime": end, "timeZone": "UTC"},
            }
            if description:
                payload["description"] = description
            if attendees:
                payload["attendees"] = [{"email": email} for email in attendees]

            with httpx.Client() as client:
                response = client.post(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                    headers={**self._get_headers(), "Content-Type": "application/json"},
                    json=payload,
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                return {
                    "success": True,
                    "id": data.get("id"),
                    "htmlLink": data.get("htmlLink"),
                }
        except Exception as e:
            logger.error(f"Google Calendar create event error: {e}")
            return {"error": str(e), "success": False}

    def _update_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
        summary: str = "",
        description: str = "",
        start: str = "",
        end: str = "",
    ) -> Dict[str, Any]:
        """Update calendar event."""
        try:
            # First get the event
            event_data = self._get_event(event_id, calendar_id)
            if not event_data.get("success"):
                return event_data

            # Build update payload
            payload = {}
            if summary:
                payload["summary"] = summary
            if description:
                payload["description"] = description
            if start:
                payload["start"] = {"dateTime": start, "timeZone": "UTC"}
            if end:
                payload["end"] = {"dateTime": end, "timeZone": "UTC"}

            with httpx.Client() as client:
                response = client.patch(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}",
                    headers={**self._get_headers(), "Content-Type": "application/json"},
                    json=payload,
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                return {"success": True, "id": data.get("id")}
        except Exception as e:
            logger.error(f"Google Calendar update event error: {e}")
            return {"error": str(e), "success": False}

    def _delete_event(self, event_id: str, calendar_id: str = "primary") -> Dict[str, Any]:
        """Delete calendar event."""
        try:
            with httpx.Client() as client:
                response = client.delete(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}",
                    headers=self._get_headers(),
                )

                if response.status_code == 204:
                    return {"success": True}
                else:
                    data = response.json()
                    return {"error": data.get("error", {}).get("message"), "success": False}
        except Exception as e:
            logger.error(f"Google Calendar delete event error: {e}")
            return {"error": str(e), "success": False}
