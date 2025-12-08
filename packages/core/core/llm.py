"""OpenAI LLM wrapper with streaming and function calling support."""

from typing import Optional, List, Dict, Any, Iterator, AsyncIterator
import openai
from openai import OpenAI, AsyncOpenAI
from loguru import logger

from .errors import LLMError


class LLM:
    """
    OpenAI GPT-based wrapper with streaming and function calling.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ):
        """
        Initialize LLM client.

        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4)
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum tokens to generate
        """
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None,
        **kwargs
    ):
        """
        Chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream responses
            functions: List of function definitions for function calling
            function_call: Function call mode ('auto', 'none', or function name)
            **kwargs: Additional OpenAI API parameters

        Returns:
            Chat completion response or stream
        """
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "stream": stream,
            }

            if self.max_tokens:
                params["max_tokens"] = self.max_tokens

            if functions:
                params["tools"] = functions
                if function_call:
                    params["tool_choice"] = function_call

            params.update(kwargs)

            if stream:
                return self.client.chat.completions.create(**params)
            else:
                return self.client.chat.completions.create(**params)

        except Exception as e:
            logger.error(f"LLM error: {e}")
            raise LLMError(f"Failed to generate completion: {e}") from e

    async def achat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None,
        **kwargs
    ):
        """
        Async chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream responses
            functions: List of function definitions for function calling
            function_call: Function call mode
            **kwargs: Additional OpenAI API parameters

        Returns:
            Async chat completion response or stream
        """
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "stream": stream,
            }

            if self.max_tokens:
                params["max_tokens"] = self.max_tokens

            if functions:
                params["tools"] = functions
                if function_call:
                    params["tool_choice"] = function_call

            params.update(kwargs)

            if stream:
                return await self.async_client.chat.completions.create(**params)
            else:
                return await self.async_client.chat.completions.create(**params)

        except Exception as e:
            logger.error(f"LLM async error: {e}")
            raise LLMError(f"Failed to generate async completion: {e}") from e

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Stream chat completion, yielding text chunks.

        Args:
            messages: List of message dicts
            functions: Function definitions
            **kwargs: Additional parameters

        Yields:
            Text chunks from the stream
        """
        try:
            stream = self.chat(messages, stream=True, functions=functions, **kwargs)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Stream error: {e}")
            raise LLMError(f"Failed to stream completion: {e}") from e

    async def astream_chat(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Async stream chat completion, yielding text chunks.

        Args:
            messages: List of message dicts
            functions: Function definitions
            **kwargs: Additional parameters

        Yields:
            Text chunks from the stream
        """
        try:
            stream = await self.achat(messages, stream=True, functions=functions, **kwargs)
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Async stream error: {e}")
            raise LLMError(f"Failed to async stream completion: {e}") from e

