"""Custom exception classes."""


class AgentFrameworkError(Exception):
    """Base exception for agent framework."""

    pass


class ConfigError(AgentFrameworkError):
    """Configuration error."""

    pass


class LLMError(AgentFrameworkError):
    """LLM operation error."""

    pass


class MemoryError(AgentFrameworkError):
    """Memory store error."""

    pass


class ToolError(AgentFrameworkError):
    """Tool execution error."""

    pass


class EmbeddingError(AgentFrameworkError):
    """Embedding generation error."""

    pass


class VectorStoreError(AgentFrameworkError):
    """Vector store operation error."""

    pass

