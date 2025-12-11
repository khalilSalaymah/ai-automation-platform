"""Stripe integration connector."""

import httpx
from typing import Dict, Any, Optional, List
from loguru import logger
from core.tools import ToolRegistry
from core.config import get_settings
from .base import BaseConnector


class StripeConnector(BaseConnector):
    """Stripe integration connector (API key based, not OAuth)."""

    def __init__(self, user_id: str, org_id: Optional[str] = None):
        super().__init__("stripe", user_id, org_id)
        self.settings = get_settings()

    def get_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Stripe uses API keys, not OAuth. Return empty string."""
        # Stripe doesn't use OAuth for server-to-server integrations
        # Instead, it uses API keys which should be stored securely
        return ""

    async def handle_oauth_callback(
        self, code: str, redirect_uri: str
    ) -> Dict[str, Any]:
        """Stripe doesn't use OAuth callbacks."""
        raise NotImplementedError("Stripe uses API keys, not OAuth")

    def set_api_key(self, api_key: str):
        """Set Stripe API key (stored as token)."""
        self.store_tokens(token=api_key)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Stripe API requests."""
        api_key = self.get_token()
        if not api_key:
            # Fallback to settings if no user-specific key
            api_key = self.settings.stripe_secret_key
        if not api_key:
            raise Exception("Stripe API key not configured")
        return {"Authorization": f"Bearer {api_key}"}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of Stripe tools."""
        return [
            {
                "name": "stripe_list_customers",
                "description": "List Stripe customers",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Number of results", "default": 10},
                        "email": {"type": "string", "description": "Filter by email"},
                    },
                    "required": [],
                },
            },
            {
                "name": "stripe_get_customer",
                "description": "Get a specific Stripe customer by ID",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string", "description": "Stripe customer ID"},
                    },
                    "required": ["customer_id"],
                },
            },
            {
                "name": "stripe_create_customer",
                "description": "Create a new Stripe customer",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "description": "Customer email"},
                        "name": {"type": "string", "description": "Customer name"},
                        "metadata": {"type": "object", "description": "Additional metadata"},
                    },
                    "required": ["email"],
                },
            },
            {
                "name": "stripe_list_subscriptions",
                "description": "List Stripe subscriptions",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string", "description": "Filter by customer ID"},
                        "limit": {"type": "integer", "description": "Number of results", "default": 10},
                    },
                    "required": [],
                },
            },
            {
                "name": "stripe_get_invoice",
                "description": "Get a Stripe invoice by ID",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "invoice_id": {"type": "string", "description": "Stripe invoice ID"},
                    },
                    "required": ["invoice_id"],
                },
            },
        ]

    def register_tools(self, registry: ToolRegistry):
        """Register Stripe tools."""
        for tool_def in self.get_tools():
            name = tool_def["name"]
            if name == "stripe_list_customers":
                registry.register_function(
                    name, tool_def["description"], self._list_customers, tool_def["parameters_schema"]
                )
            elif name == "stripe_get_customer":
                registry.register_function(
                    name, tool_def["description"], self._get_customer, tool_def["parameters_schema"]
                )
            elif name == "stripe_create_customer":
                registry.register_function(
                    name, tool_def["description"], self._create_customer, tool_def["parameters_schema"]
                )
            elif name == "stripe_list_subscriptions":
                registry.register_function(
                    name, tool_def["description"], self._list_subscriptions, tool_def["parameters_schema"]
                )
            elif name == "stripe_get_invoice":
                registry.register_function(
                    name, tool_def["description"], self._get_invoice, tool_def["parameters_schema"]
                )

    def _list_customers(self, limit: int = 10, email: str = "") -> Dict[str, Any]:
        """List Stripe customers."""
        try:
            params = {"limit": limit}
            if email:
                params["email"] = email

            with httpx.Client() as client:
                response = client.get(
                    "https://api.stripe.com/v1/customers",
                    headers=self._get_headers(),
                    params=params,
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                customers = [
                    {
                        "id": c.get("id"),
                        "email": c.get("email"),
                        "name": c.get("name"),
                        "created": c.get("created"),
                    }
                    for c in data.get("data", [])
                ]
                return {"success": True, "customers": customers}
        except Exception as e:
            logger.error(f"Stripe list customers error: {e}")
            return {"error": str(e), "success": False}

    def _get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Get specific Stripe customer."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"https://api.stripe.com/v1/customers/{customer_id}",
                    headers=self._get_headers(),
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                return {
                    "success": True,
                    "id": data.get("id"),
                    "email": data.get("email"),
                    "name": data.get("name"),
                    "created": data.get("created"),
                    "balance": data.get("balance"),
                }
        except Exception as e:
            logger.error(f"Stripe get customer error: {e}")
            return {"error": str(e), "success": False}

    def _create_customer(
        self, email: str, name: str = "", metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create Stripe customer."""
        try:
            payload = {"email": email}
            if name:
                payload["name"] = name
            if metadata:
                payload["metadata"] = metadata

            with httpx.Client() as client:
                response = client.post(
                    "https://api.stripe.com/v1/customers",
                    headers={**self._get_headers(), "Content-Type": "application/x-www-form-urlencoded"},
                    data=payload,
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                return {
                    "success": True,
                    "id": data.get("id"),
                    "email": data.get("email"),
                }
        except Exception as e:
            logger.error(f"Stripe create customer error: {e}")
            return {"error": str(e), "success": False}

    def _list_subscriptions(self, customer_id: str = "", limit: int = 10) -> Dict[str, Any]:
        """List Stripe subscriptions."""
        try:
            params = {"limit": limit}
            if customer_id:
                params["customer"] = customer_id

            with httpx.Client() as client:
                response = client.get(
                    "https://api.stripe.com/v1/subscriptions",
                    headers=self._get_headers(),
                    params=params,
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                subscriptions = [
                    {
                        "id": s.get("id"),
                        "customer": s.get("customer"),
                        "status": s.get("status"),
                        "current_period_end": s.get("current_period_end"),
                    }
                    for s in data.get("data", [])
                ]
                return {"success": True, "subscriptions": subscriptions}
        except Exception as e:
            logger.error(f"Stripe list subscriptions error: {e}")
            return {"error": str(e), "success": False}

    def _get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """Get Stripe invoice."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"https://api.stripe.com/v1/invoices/{invoice_id}",
                    headers=self._get_headers(),
                )
                data = response.json()

                if "error" in data:
                    return {"error": data["error"], "success": False}

                return {
                    "success": True,
                    "id": data.get("id"),
                    "customer": data.get("customer"),
                    "amount_due": data.get("amount_due"),
                    "status": data.get("status"),
                    "created": data.get("created"),
                }
        except Exception as e:
            logger.error(f"Stripe get invoice error: {e}")
            return {"error": str(e), "success": False}
