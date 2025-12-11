"""Airtable integration connector with OAuth."""

import httpx
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode
from loguru import logger
from core.tools import ToolRegistry
from core.config import get_settings
from .base import BaseConnector


class AirtableConnector(BaseConnector):
    """Airtable integration connector with OAuth."""

    def __init__(self, user_id: str, org_id: Optional[str] = None):
        super().__init__("airtable", user_id, org_id)
        self.settings = get_settings()

    def get_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Generate Airtable OAuth authorization URL."""
        client_id = self.settings.airtable_client_id
        scopes = ["data.records:read", "data.records:write", "schema.bases:read"]
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "response_type": "code",
            "state": state or "",
        }

        return f"https://airtable.com/oauth2/v1/authorize?{urlencode(params)}"

    async def handle_oauth_callback(
        self, code: str, redirect_uri: str
    ) -> Dict[str, Any]:
        """Handle Airtable OAuth callback."""
        client_id = self.settings.airtable_client_id
        client_secret = self.settings.airtable_client_secret

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://airtable.com/oauth2/v1/token",
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
                raise Exception(f"Airtable OAuth error: {data.get('error')}")

            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")

            self.store_tokens(
                token=access_token,
                refresh_token=refresh_token,
            )

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Airtable API requests."""
        token = self.get_token()
        if not token:
            raise Exception("Not authenticated with Airtable")
        return {"Authorization": f"Bearer {token}"}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of Airtable tools."""
        return [
            {
                "name": "airtable_list_bases",
                "description": "List all Airtable bases",
                "parameters_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "airtable_list_tables",
                "description": "List tables in an Airtable base",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "base_id": {"type": "string", "description": "Airtable base ID"},
                    },
                    "required": ["base_id"],
                },
            },
            {
                "name": "airtable_list_records",
                "description": "List records from an Airtable table",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "base_id": {"type": "string", "description": "Airtable base ID"},
                        "table_id": {"type": "string", "description": "Airtable table ID or name"},
                        "max_records": {"type": "integer", "description": "Maximum number of records", "default": 100},
                    },
                    "required": ["base_id", "table_id"],
                },
            },
            {
                "name": "airtable_get_record",
                "description": "Get a specific record from Airtable",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "base_id": {"type": "string", "description": "Airtable base ID"},
                        "table_id": {"type": "string", "description": "Airtable table ID or name"},
                        "record_id": {"type": "string", "description": "Record ID"},
                    },
                    "required": ["base_id", "table_id", "record_id"],
                },
            },
            {
                "name": "airtable_create_record",
                "description": "Create a new record in Airtable",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "base_id": {"type": "string", "description": "Airtable base ID"},
                        "table_id": {"type": "string", "description": "Airtable table ID or name"},
                        "fields": {"type": "object", "description": "Record fields"},
                    },
                    "required": ["base_id", "table_id", "fields"],
                },
            },
            {
                "name": "airtable_update_record",
                "description": "Update a record in Airtable",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "base_id": {"type": "string", "description": "Airtable base ID"},
                        "table_id": {"type": "string", "description": "Airtable table ID or name"},
                        "record_id": {"type": "string", "description": "Record ID"},
                        "fields": {"type": "object", "description": "Fields to update"},
                    },
                    "required": ["base_id", "table_id", "record_id", "fields"],
                },
            },
        ]

    def register_tools(self, registry: ToolRegistry):
        """Register Airtable tools."""
        for tool_def in self.get_tools():
            name = tool_def["name"]
            if name == "airtable_list_bases":
                registry.register_function(
                    name, tool_def["description"], self._list_bases, tool_def["parameters_schema"]
                )
            elif name == "airtable_list_tables":
                registry.register_function(
                    name, tool_def["description"], self._list_tables, tool_def["parameters_schema"]
                )
            elif name == "airtable_list_records":
                registry.register_function(
                    name, tool_def["description"], self._list_records, tool_def["parameters_schema"]
                )
            elif name == "airtable_get_record":
                registry.register_function(
                    name, tool_def["description"], self._get_record, tool_def["parameters_schema"]
                )
            elif name == "airtable_create_record":
                registry.register_function(
                    name, tool_def["description"], self._create_record, tool_def["parameters_schema"]
                )
            elif name == "airtable_update_record":
                registry.register_function(
                    name, tool_def["description"], self._update_record, tool_def["parameters_schema"]
                )

    def _list_bases(self) -> Dict[str, Any]:
        """List Airtable bases."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    "https://api.airtable.com/v0/meta/bases",
                    headers=self._get_headers(),
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                bases = [
                    {"id": base.get("id"), "name": base.get("name")}
                    for base in data.get("bases", [])
                ]
                return {"success": True, "bases": bases}
        except Exception as e:
            logger.error(f"Airtable list bases error: {e}")
            return {"error": str(e), "success": False}

    def _list_tables(self, base_id: str) -> Dict[str, Any]:
        """List tables in a base."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"https://api.airtable.com/v0/meta/bases/{base_id}/tables",
                    headers=self._get_headers(),
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                tables = [
                    {"id": table.get("id"), "name": table.get("name")}
                    for table in data.get("tables", [])
                ]
                return {"success": True, "tables": tables}
        except Exception as e:
            logger.error(f"Airtable list tables error: {e}")
            return {"error": str(e), "success": False}

    def _list_records(self, base_id: str, table_id: str, max_records: int = 100) -> Dict[str, Any]:
        """List records from a table."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"https://api.airtable.com/v0/{base_id}/{table_id}",
                    headers=self._get_headers(),
                    params={"maxRecords": max_records},
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                records = [
                    {"id": record.get("id"), "fields": record.get("fields", {})}
                    for record in data.get("records", [])
                ]
                return {"success": True, "records": records}
        except Exception as e:
            logger.error(f"Airtable list records error: {e}")
            return {"error": str(e), "success": False}

    def _get_record(self, base_id: str, table_id: str, record_id: str) -> Dict[str, Any]:
        """Get specific record."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"https://api.airtable.com/v0/{base_id}/{table_id}/{record_id}",
                    headers=self._get_headers(),
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                return {
                    "success": True,
                    "id": data.get("id"),
                    "fields": data.get("fields", {}),
                }
        except Exception as e:
            logger.error(f"Airtable get record error: {e}")
            return {"error": str(e), "success": False}

    def _create_record(self, base_id: str, table_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Create record."""
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"https://api.airtable.com/v0/{base_id}/{table_id}",
                    headers={**self._get_headers(), "Content-Type": "application/json"},
                    json={"fields": fields},
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                return {
                    "success": True,
                    "id": data.get("id"),
                    "fields": data.get("fields", {}),
                }
        except Exception as e:
            logger.error(f"Airtable create record error: {e}")
            return {"error": str(e), "success": False}

    def _update_record(
        self, base_id: str, table_id: str, record_id: str, fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update record."""
        try:
            with httpx.Client() as client:
                response = client.patch(
                    f"https://api.airtable.com/v0/{base_id}/{table_id}/{record_id}",
                    headers={**self._get_headers(), "Content-Type": "application/json"},
                    json={"fields": fields},
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                return {
                    "success": True,
                    "id": data.get("id"),
                    "fields": data.get("fields", {}),
                }
        except Exception as e:
            logger.error(f"Airtable update record error: {e}")
            return {"error": str(e), "success": False}
