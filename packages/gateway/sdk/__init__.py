"""Python SDK for AI Automation Platform Gateway."""

from .client import GatewayClient
from .exceptions import GatewayError, AuthenticationError, QuotaExceededError, RateLimitError

__all__ = [
    "GatewayClient",
    "GatewayError",
    "AuthenticationError",
    "QuotaExceededError",
    "RateLimitError",
]

__version__ = "0.1.0"
