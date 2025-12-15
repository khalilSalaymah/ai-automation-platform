"""Multi-provider LLM wrapper with Groq and Gemini support."""

import time
from typing import Optional, Dict, Any
from loguru import logger

from .errors import LLMError, ConfigError
from .logger import (
    get_trace_id,
    generate_span_id,
    set_span_id,
    get_span_id,
    log_span,
)
from .observability import log_error_with_alert
from .config import get_env


class LLM:
    """
    Multi-provider LLM wrapper supporting Groq and Gemini.
    Provider is detected from LLM_PROVIDER environment variable.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ):
        """
        Initialize LLM client.

        Args:
            api_key: Provider API key (optional, will load from env if not provided)
            model: Model name (optional, will use provider default if not provided)
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum tokens to generate
        """
        # Detect provider from environment
        self.provider = get_env("LLM_PROVIDER", "groq").lower()
        
        if self.provider not in ["groq", "gemini"]:
            raise ConfigError(
                f"Unsupported LLM provider: {self.provider}. "
                "Supported providers: 'groq', 'gemini'"
            )

        # Load provider-specific configuration
        if self.provider == "groq":
            self._init_groq(api_key, model, temperature, max_tokens)
        elif self.provider == "gemini":
            self._init_gemini(api_key, model, temperature, max_tokens)

    def _init_groq(
        self,
        api_key: Optional[str],
        model: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ):
        """Initialize Groq client."""
        try:
            from groq import Groq
        except ImportError:
            raise ConfigError(
                "Groq SDK not installed. Install with: pip install groq"
            )

        # Load API key
        if not api_key:
            api_key = get_env("GROQ_API_KEY")
        if not api_key:
            raise ConfigError("GROQ_API_KEY not found in environment variables")

        self.client = Groq(api_key=api_key)
        # Allow overriding the Groq model via environment to avoid breakage
        # when models are deprecated by the provider.
        # If GROQ_MODEL is not set, fall back to a reasonable default.
        env_model = get_env("GROQ_MODEL")
        self.model = model or env_model or "llama-3.1-8b-instant"
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _init_gemini(
        self,
        api_key: Optional[str],
        model: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ):
        """Initialize Gemini client."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ConfigError(
                "Google Generative AI SDK not installed. "
                "Install with: pip install google-generativeai"
            )

        # Load API key
        if not api_key:
            api_key = get_env("GEMINI_API_KEY")
        if not api_key:
            raise ConfigError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        self.genai = genai
        # Use a broadly available default model for the current Gemini API.
        # If a specific model is needed, it can be passed explicitly when
        # constructing LLM or via a higher-level service.
        self.model_name = model or "gemini-pro"
        self.temperature = temperature
        self.max_tokens = max_tokens

    def chat(
        self,
        prompt: str,
        tools: Optional[list] = None,
        **kwargs
    ) -> str:
        """
        Chat completion with span tracking.

        Args:
            prompt: User prompt string
            tools: Optional list of tool definitions for function calling
            **kwargs: Additional provider-specific parameters

        Returns:
            Response text as string
        """
        start_time = time.time()
        parent_span_id = get_span_id()
        span_id = generate_span_id()
        set_span_id(span_id, parent_span_id)
        trace_id = get_trace_id()

        try:
            # Log LLM call start
            logger.info(
                "LLM call started",
                provider=self.provider,
                model=self.model if self.provider == "groq" else self.model_name,
                has_tools=bool(tools),
            )

            if self.provider == "groq":
                response_text = self._chat_groq(prompt, tools, **kwargs)
            elif self.provider == "gemini":
                response_text = self._chat_gemini(prompt, tools, **kwargs)
            else:
                raise ConfigError(f"Unsupported provider: {self.provider}")

            end_time = time.time()

            # Log span
            log_span(
                operation="llm_call",
                service=self.provider,
                metadata={
                    "model": self.model if self.provider == "groq" else self.model_name,
                    "has_tools": bool(tools),
                    "provider": self.provider,
                },
                start_time=start_time,
                end_time=end_time,
            )

            return response_text

        except Exception as e:
            end_time = time.time()

            # Log error span
            log_span(
                operation="llm_call",
                service=self.provider,
                metadata={
                    "model": self.model if self.provider == "groq" else self.model_name,
                    "has_tools": bool(tools),
                    "provider": self.provider,
                },
                start_time=start_time,
                end_time=end_time,
                error=str(e),
            )

            log_error_with_alert(
                message=f"LLM call failed: {self.provider}",
                error=e,
                metadata={
                    "model": self.model if self.provider == "groq" else self.model_name,
                    "has_tools": bool(tools),
                    "provider": self.provider,
                },
            )

            raise LLMError(f"Failed to generate completion: {e}") from e

    def _chat_groq(
        self,
        prompt: str,
        tools: Optional[list],
        **kwargs
    ) -> str:
        """Execute chat with Groq provider."""
        messages = [{"role": "user", "content": prompt}]

        params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }

        if self.max_tokens:
            params["max_tokens"] = self.max_tokens

        # Groq uses 'tools' parameter for function calling
        if tools:
            params["tools"] = tools

        params.update(kwargs)

        response = self.client.chat.completions.create(**params)
        return response.choices[0].message.content

    def _chat_gemini(
        self,
        prompt: str,
        tools: Optional[list],
        **kwargs
    ) -> str:
        """Execute chat with Gemini provider."""
        generation_config = {
            "temperature": self.temperature,
        }

        if self.max_tokens:
            generation_config["max_output_tokens"] = self.max_tokens

        # Merge with kwargs (kwargs take precedence)
        generation_config.update(kwargs)

        # Gemini uses function_declarations for tools
        gemini_tools = None
        if tools:
            # Convert tools format to Gemini's function_declarations format
            function_declarations = []
            for tool in tools:
                if isinstance(tool, dict):
                    func = tool.get("function", {})
                    func_decl = {
                        "name": func.get("name", ""),
                        "description": func.get("description", ""),
                        "parameters": func.get("parameters", {}),
                    }
                    function_declarations.append(func_decl)
            
            if function_declarations:
                gemini_tools = [{"function_declarations": function_declarations}]

        # Create model with tools and generation config
        model = self.genai.GenerativeModel(
            self.model_name,
            generation_config=generation_config,
            tools=gemini_tools,
        )

        response = model.generate_content(prompt)
        return response.text
