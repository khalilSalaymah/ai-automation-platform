"""Base connector class for all integrations."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlmodel import Session, select
from loguru import logger
from core.tools import ToolRegistry
from core.database import get_session
from .models import IntegrationToken


class BaseConnector(ABC):
    """Base class for all integration connectors."""

    def __init__(self, name: str, user_id: str, org_id: Optional[str] = None):
        """
        Initialize connector.

        Args:
            name: Integration name (e.g., "slack", "gmail")
            user_id: User ID for token storage
            org_id: Optional organization ID
        """
        self.name = name
        self.user_id = user_id
        self.org_id = org_id
        self._token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    @abstractmethod
    def get_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """
        Generate OAuth authorization URL.

        Args:
            redirect_uri: OAuth redirect URI
            state: Optional state parameter for CSRF protection

        Returns:
            OAuth authorization URL
        """
        raise NotImplementedError

    @abstractmethod
    async def handle_oauth_callback(
        self, code: str, redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Handle OAuth callback and exchange code for tokens.

        Args:
            code: OAuth authorization code
            redirect_uri: OAuth redirect URI

        Returns:
            Dictionary with token information
        """
        raise NotImplementedError

    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of tools provided by this connector.

        Returns:
            List of tool definitions with name, description, and parameters_schema
        """
        raise NotImplementedError

    @abstractmethod
    def register_tools(self, registry: ToolRegistry):
        """
        Register all tools from this connector to the tool registry.

        Args:
            registry: ToolRegistry instance
        """
        raise NotImplementedError

    def store_tokens(
        self,
        token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session: Optional[Session] = None,
    ):
        """
        Store encrypted tokens in database.

        Args:
            token: OAuth access token
            refresh_token: Optional refresh token
            expires_at: Optional token expiration time
            metadata: Optional metadata dictionary
        """
        if session is None:
            session_gen = get_session()
            session = next(session_gen)

        # Check if token already exists
        statement = select(IntegrationToken).where(
            IntegrationToken.user_id == self.user_id,
            IntegrationToken.integration_name == self.name,
        )
        if self.org_id:
            statement = statement.where(IntegrationToken.org_id == self.org_id)

        existing = session.exec(statement).first()

        if existing:
            token_model = existing
        else:
            token_model = IntegrationToken(
                user_id=self.user_id,
                org_id=self.org_id,
                integration_name=self.name,
            )

        token_model.set_token(token, refresh_token)
        token_model.expires_at = expires_at
        if metadata:
            import json
            token_model.metadata = json.dumps(metadata)

        if not existing:
            session.add(token_model)

        session.commit()
        session.refresh(token_model)

        self._token = token
        self._refresh_token = refresh_token

        logger.info(f"Stored tokens for {self.name} integration")

    def load_tokens(self, session: Optional[Session] = None) -> bool:
        """
        Load tokens from database.

        Args:
            session: Optional database session

        Returns:
            True if tokens were loaded, False otherwise
        """
        if session is None:
            session_gen = get_session()
            session = next(session_gen)

        statement = select(IntegrationToken).where(
            IntegrationToken.user_id == self.user_id,
            IntegrationToken.integration_name == self.name,
        )
        if self.org_id:
            statement = statement.where(IntegrationToken.org_id == self.org_id)

        token_model = session.exec(statement).first()

        if not token_model:
            return False

        try:
            self._token = token_model.get_token()
            self._refresh_token = token_model.get_refresh_token()
            return True
        except Exception as e:
            logger.error(f"Failed to load tokens for {self.name}: {e}")
            return False

    def get_token(self) -> Optional[str]:
        """Get current access token."""
        if not self._token:
            self.load_tokens()
        return self._token

    def refresh_access_token(self) -> bool:
        """
        Refresh access token using refresh token.

        Returns:
            True if refresh was successful, False otherwise
        """
        if not self._refresh_token:
            if not self.load_tokens():
                return False

        # Subclasses should implement token refresh logic
        logger.warning(f"Token refresh not implemented for {self.name}")
        return False

    def is_authenticated(self) -> bool:
        """Check if connector has valid authentication."""
        return self.get_token() is not None
