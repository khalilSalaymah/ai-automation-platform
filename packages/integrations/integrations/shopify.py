"""Shopify integration connector with OAuth."""

import httpx
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode
from loguru import logger
from core.tools import ToolRegistry
from core.config import get_settings
from .base import BaseConnector


class ShopifyConnector(BaseConnector):
    """Shopify integration connector with OAuth."""

    def __init__(self, user_id: str, org_id: Optional[str] = None):
        super().__init__("shopify", user_id, org_id)
        self.settings = get_settings()

    def get_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Generate Shopify OAuth authorization URL."""
        client_id = self.settings.shopify_client_id
        shop = self.settings.shopify_shop_name  # e.g., "my-shop"
        scopes = [
            "read_products",
            "write_products",
            "read_orders",
            "read_customers",
            "write_customers",
        ]
        params = {
            "client_id": client_id,
            "scope": ",".join(scopes),
            "redirect_uri": redirect_uri,
        }
        if state:
            params["state"] = state

        return f"https://{shop}.myshopify.com/admin/oauth/authorize?{urlencode(params)}"

    async def handle_oauth_callback(
        self, code: str, redirect_uri: str
    ) -> Dict[str, Any]:
        """Handle Shopify OAuth callback."""
        client_id = self.settings.shopify_client_id
        client_secret = self.settings.shopify_client_secret
        shop = self.settings.shopify_shop_name

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{shop}.myshopify.com/admin/oauth/access_token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                },
            )
            data = response.json()

            if "error" in data:
                raise Exception(f"Shopify OAuth error: {data.get('error')}")

            access_token = data.get("access_token")
            shop_name = data.get("shop", shop)

            self.store_tokens(
                token=access_token,
                metadata={"shop": shop_name},
            )

            return {
                "access_token": access_token,
                "shop": shop_name,
            }

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Shopify API requests."""
        token = self.get_token()
        if not token:
            raise Exception("Not authenticated with Shopify")
        shop = self.settings.shopify_shop_name
        return {
            "X-Shopify-Access-Token": token,
            "Content-Type": "application/json",
        }

    def _get_base_url(self) -> str:
        """Get Shopify API base URL."""
        shop = self.settings.shopify_shop_name
        return f"https://{shop}.myshopify.com/admin/api/2024-01"

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of Shopify tools."""
        return [
            {
                "name": "shopify_list_products",
                "description": "List products from Shopify store",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Number of results", "default": 50},
                        "title": {"type": "string", "description": "Filter by product title"},
                    },
                    "required": [],
                },
            },
            {
                "name": "shopify_get_product",
                "description": "Get a specific product by ID",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "string", "description": "Shopify product ID"},
                    },
                    "required": ["product_id"],
                },
            },
            {
                "name": "shopify_create_product",
                "description": "Create a new product in Shopify",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Product title"},
                        "body_html": {"type": "string", "description": "Product description (HTML)"},
                        "vendor": {"type": "string", "description": "Product vendor"},
                        "product_type": {"type": "string", "description": "Product type"},
                        "variants": {"type": "array", "items": {"type": "object"}, "description": "Product variants"},
                    },
                    "required": ["title"],
                },
            },
            {
                "name": "shopify_list_orders",
                "description": "List orders from Shopify store",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Number of results", "default": 50},
                        "status": {"type": "string", "description": "Filter by order status"},
                    },
                    "required": [],
                },
            },
            {
                "name": "shopify_get_order",
                "description": "Get a specific order by ID",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string", "description": "Shopify order ID"},
                    },
                    "required": ["order_id"],
                },
            },
            {
                "name": "shopify_list_customers",
                "description": "List customers from Shopify store",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Number of results", "default": 50},
                        "email": {"type": "string", "description": "Filter by email"},
                    },
                    "required": [],
                },
            },
        ]

    def register_tools(self, registry: ToolRegistry):
        """Register Shopify tools."""
        for tool_def in self.get_tools():
            name = tool_def["name"]
            if name == "shopify_list_products":
                registry.register_function(
                    name, tool_def["description"], self._list_products, tool_def["parameters_schema"]
                )
            elif name == "shopify_get_product":
                registry.register_function(
                    name, tool_def["description"], self._get_product, tool_def["parameters_schema"]
                )
            elif name == "shopify_create_product":
                registry.register_function(
                    name, tool_def["description"], self._create_product, tool_def["parameters_schema"]
                )
            elif name == "shopify_list_orders":
                registry.register_function(
                    name, tool_def["description"], self._list_orders, tool_def["parameters_schema"]
                )
            elif name == "shopify_get_order":
                registry.register_function(
                    name, tool_def["description"], self._get_order, tool_def["parameters_schema"]
                )
            elif name == "shopify_list_customers":
                registry.register_function(
                    name, tool_def["description"], self._list_customers, tool_def["parameters_schema"]
                )

    def _list_products(self, limit: int = 50, title: str = "") -> Dict[str, Any]:
        """List Shopify products."""
        try:
            params = {"limit": limit}
            if title:
                params["title"] = title

            with httpx.Client() as client:
                response = client.get(
                    f"{self._get_base_url()}/products.json",
                    headers=self._get_headers(),
                    params=params,
                )
                data = response.json()

                if "errors" in data:
                    return {"error": data["errors"], "success": False}

                products = [
                    {
                        "id": p.get("id"),
                        "title": p.get("title"),
                        "vendor": p.get("vendor"),
                        "product_type": p.get("product_type"),
                    }
                    for p in data.get("products", [])
                ]
                return {"success": True, "products": products}
        except Exception as e:
            logger.error(f"Shopify list products error: {e}")
            return {"error": str(e), "success": False}

    def _get_product(self, product_id: str) -> Dict[str, Any]:
        """Get specific Shopify product."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self._get_base_url()}/products/{product_id}.json",
                    headers=self._get_headers(),
                )
                data = response.json()

                if "errors" in data:
                    return {"error": data["errors"], "success": False}

                product = data.get("product", {})
                return {
                    "success": True,
                    "id": product.get("id"),
                    "title": product.get("title"),
                    "body_html": product.get("body_html"),
                    "vendor": product.get("vendor"),
                    "variants": product.get("variants", []),
                }
        except Exception as e:
            logger.error(f"Shopify get product error: {e}")
            return {"error": str(e), "success": False}

    def _create_product(
        self,
        title: str,
        body_html: str = "",
        vendor: str = "",
        product_type: str = "",
        variants: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Create Shopify product."""
        try:
            payload = {
                "product": {
                    "title": title,
                }
            }
            if body_html:
                payload["product"]["body_html"] = body_html
            if vendor:
                payload["product"]["vendor"] = vendor
            if product_type:
                payload["product"]["product_type"] = product_type
            if variants:
                payload["product"]["variants"] = variants

            with httpx.Client() as client:
                response = client.post(
                    f"{self._get_base_url()}/products.json",
                    headers=self._get_headers(),
                    json=payload,
                )
                data = response.json()

                if "errors" in data:
                    return {"error": data["errors"], "success": False}

                product = data.get("product", {})
                return {
                    "success": True,
                    "id": product.get("id"),
                    "title": product.get("title"),
                }
        except Exception as e:
            logger.error(f"Shopify create product error: {e}")
            return {"error": str(e), "success": False}

    def _list_orders(self, limit: int = 50, status: str = "") -> Dict[str, Any]:
        """List Shopify orders."""
        try:
            params = {"limit": limit}
            if status:
                params["status"] = status

            with httpx.Client() as client:
                response = client.get(
                    f"{self._get_base_url()}/orders.json",
                    headers=self._get_headers(),
                    params=params,
                )
                data = response.json()

                if "errors" in data:
                    return {"error": data["errors"], "success": False}

                orders = [
                    {
                        "id": o.get("id"),
                        "order_number": o.get("order_number"),
                        "email": o.get("email"),
                        "total_price": o.get("total_price"),
                        "financial_status": o.get("financial_status"),
                    }
                    for o in data.get("orders", [])
                ]
                return {"success": True, "orders": orders}
        except Exception as e:
            logger.error(f"Shopify list orders error: {e}")
            return {"error": str(e), "success": False}

    def _get_order(self, order_id: str) -> Dict[str, Any]:
        """Get specific Shopify order."""
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self._get_base_url()}/orders/{order_id}.json",
                    headers=self._get_headers(),
                )
                data = response.json()

                if "errors" in data:
                    return {"error": data["errors"], "success": False}

                order = data.get("order", {})
                return {
                    "success": True,
                    "id": order.get("id"),
                    "order_number": order.get("order_number"),
                    "email": order.get("email"),
                    "total_price": order.get("total_price"),
                    "line_items": order.get("line_items", []),
                }
        except Exception as e:
            logger.error(f"Shopify get order error: {e}")
            return {"error": str(e), "success": False}

    def _list_customers(self, limit: int = 50, email: str = "") -> Dict[str, Any]:
        """List Shopify customers."""
        try:
            params = {"limit": limit}
            if email:
                params["email"] = email

            with httpx.Client() as client:
                response = client.get(
                    f"{self._get_base_url()}/customers.json",
                    headers=self._get_headers(),
                    params=params,
                )
                data = response.json()

                if "errors" in data:
                    return {"error": data["errors"], "success": False}

                customers = [
                    {
                        "id": c.get("id"),
                        "email": c.get("email"),
                        "first_name": c.get("first_name"),
                        "last_name": c.get("last_name"),
                    }
                    for c in data.get("customers", [])
                ]
                return {"success": True, "customers": customers}
        except Exception as e:
            logger.error(f"Shopify list customers error: {e}")
            return {"error": str(e), "success": False}
