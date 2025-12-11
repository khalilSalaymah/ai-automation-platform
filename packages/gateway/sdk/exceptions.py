"""Gateway SDK exceptions."""


class GatewayError(Exception):
    """Base exception for gateway errors."""

    pass


class AuthenticationError(GatewayError):
    """Authentication error (401)."""

    pass


class QuotaExceededError(GatewayError):
    """Quota exceeded error (402)."""

    pass


class RateLimitError(GatewayError):
    """Rate limit exceeded error (429)."""

    pass
