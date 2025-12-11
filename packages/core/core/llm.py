"""OpenAI LLM wrapper with streaming and function calling support."""

import time
from typing import Optional, List, Dict, Any, Iterator, AsyncIterator
import openai
from openai import OpenAI, AsyncOpenAI
from loguru import logger

from .errors import LLMError
from .logger import (
    get_trace_id,
    generate_span_id,
    set_span_id,
    get_span_id,
    log_span,
)
from .observability import log_error_with_alert


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
        Chat completion with span tracking.

        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream responses
            functions: List of function definitions for function calling
            function_call: Function call mode ('auto', 'none', or function name)
            **kwargs: Additional OpenAI API parameters

        Returns:
            Chat completion response or stream
        """
        start_time = time.time()
        parent_span_id = get_span_id()
        span_id = generate_span_id()
        set_span_id(span_id, parent_span_id)
        trace_id = get_trace_id()
        
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

            # Log LLM call start
            logger.info(
                "LLM call started",
                model=self.model,
                has_functions=bool(functions),
                stream=stream,
            )

            if stream:
                result = self.client.chat.completions.create(**params)
            else:
                result = self.client.chat.completions.create(**params)
            
            end_time = time.time()
            
            # Log span
            log_span(
                operation="llm_call",
                service="openai",
                metadata={
                    "model": self.model,
                    "has_functions": bool(functions),
                    "stream": stream,
                    "messages_count": len(messages),
                },
                start_time=start_time,
                end_time=end_time,
            )
            
            return result

        except Exception as e:
            end_time = time.time()
            
            # Log error span
            log_span(
                operation="llm_call",
                service="openai",
                metadata={
                    "model": self.model,
                    "has_functions": bool(functions),
                    "stream": stream,
                },
                start_time=start_time,
                end_time=end_time,
                error=str(e),
            )
            
            log_error_with_alert(
                message=f"LLM call failed: {self.model}",
                error=e,
                metadata={
                    "model": self.model,
                    "has_functions": bool(functions),
                },
            )
            
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
        Async chat completion with span tracking.

        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream responses
            functions: List of function definitions for function calling
            function_call: Function call mode
            **kwargs: Additional OpenAI API parameters

        Returns:
            Async chat completion response or stream
        """
        start_time = time.time()
        parent_span_id = get_span_id()
        span_id = generate_span_id()
        set_span_id(span_id, parent_span_id)
        trace_id = get_trace_id()
        
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

            # Log LLM call start
            logger.info(
                "LLM async call started",
                model=self.model,
                has_functions=bool(functions),
                stream=stream,
            )

            if stream:
                result = await self.async_client.chat.completions.create(**params)
            else:
                result = await self.async_client.chat.completions.create(**params)
            
            end_time = time.time()
            
            # Log span
            log_span(
                operation="llm_call",
                service="openai",
                metadata={
                    "model": self.model,
                    "has_functions": bool(functions),
                    "stream": stream,
                    "messages_count": len(messages),
                },
                start_time=start_time,
                end_time=end_time,
            )
            
            return result

        except Exception as e:
            end_time = time.time()
            
            # Log error span
            log_span(
                operation="llm_call",
                service="openai",
                metadata={
                    "model": self.model,
                    "has_functions": bool(functions),
                    "stream": stream,
                },
                start_time=start_time,
                end_time=end_time,
                error=str(e),
            )
            
            log_error_with_alert(
                message=f"LLM async call failed: {self.model}",
                error=e,
                metadata={
                    "model": self.model,
                    "has_functions": bool(functions),
                },
            )
            
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

