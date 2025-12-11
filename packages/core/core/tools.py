"""Tool registry and standardized tool interface."""

import time
from typing import Callable, Dict, Any, List, Optional
from abc import ABC, abstractmethod
from loguru import logger

from .errors import ToolError
from .logger import (
    get_trace_id,
    generate_span_id,
    set_span_id,
    get_span_id,
    log_span,
)
from .observability import log_error_with_alert


class Tool(ABC):
    """
    Standard tool interface: run(input_dict) -> output_dict
    """

    def __init__(self, name: str, description: str):
        """
        Initialize tool.

        Args:
            name: Tool name (must be unique)
            description: Tool description for LLM
        """
        self.name = name
        self.description = description

    @abstractmethod
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tool with given inputs.

        Args:
            inputs: Input parameters dictionary

        Returns:
            Output dictionary with results
        """
        raise NotImplementedError

    def to_function_schema(self) -> Dict[str, Any]:
        """
        Convert tool to OpenAI function calling schema.

        Returns:
            Function schema dictionary
        """
        # This should be overridden by subclasses
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }


class FunctionTool(Tool):
    """Tool wrapper for Python functions."""

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters_schema: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize function tool.

        Args:
            name: Tool name
            description: Tool description
            func: Python function to wrap
            parameters_schema: OpenAI function parameters schema
        """
        super().__init__(name, description)
        self.func = func
        self.parameters_schema = parameters_schema or {}

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute wrapped function with span tracking."""
        start_time = time.time()
        parent_span_id = get_span_id()
        span_id = generate_span_id()
        set_span_id(span_id, parent_span_id)
        trace_id = get_trace_id()
        
        try:
            # Log tool execution start
            logger.info(
                "Tool execution started",
                tool_name=self.name,
                inputs_keys=list(inputs.keys()),
            )
            
            result = self.func(**inputs)
            
            end_time = time.time()
            
            # Log span
            log_span(
                operation="tool_execution",
                service="tool_registry",
                metadata={
                    "tool_name": self.name,
                    "inputs_keys": list(inputs.keys()),
                },
                start_time=start_time,
                end_time=end_time,
            )
            
            return {"result": result, "success": True}
        except Exception as e:
            end_time = time.time()
            
            # Log error span
            log_span(
                operation="tool_execution",
                service="tool_registry",
                metadata={
                    "tool_name": self.name,
                    "inputs_keys": list(inputs.keys()),
                },
                start_time=start_time,
                end_time=end_time,
                error=str(e),
            )
            
            log_error_with_alert(
                message=f"Tool execution failed: {self.name}",
                error=e,
                metadata={
                    "tool_name": self.name,
                    "inputs_keys": list(inputs.keys()),
                },
            )
            
            logger.error(f"Tool {self.name} error: {e}")
            return {"result": None, "success": False, "error": str(e)}

    def to_function_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI function schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema or {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }


class ToolRegistry:
    """Registry for managing tools."""

    def __init__(self):
        """Initialize tool registry."""
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """
        Register a tool.

        Args:
            tool: Tool instance to register

        Raises:
            ToolError: If tool name already exists
        """
        if tool.name in self.tools:
            raise ToolError(f"Tool '{tool.name}' already registered")
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def register_function(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters_schema: Optional[Dict[str, Any]] = None,
    ):
        """
        Register a function as a tool.

        Args:
            name: Tool name
            description: Tool description
            func: Python function
            parameters_schema: OpenAI function parameters schema
        """
        tool = FunctionTool(name, description, func, parameters_schema)
        self.register(tool)

    def get(self, name: str) -> Optional[Tool]:
        """
        Get tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self.tools.get(name)

    def list(self) -> List[str]:
        """
        List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())

    def get_function_schemas(self) -> List[Dict[str, Any]]:
        """
        Get OpenAI function schemas for all registered tools.

        Returns:
            List of function schema dictionaries
        """
        return [tool.to_function_schema() for tool in self.tools.values()]

    def execute(self, name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name with span tracking.

        Args:
            name: Tool name
            inputs: Input parameters

        Returns:
            Tool execution result

        Raises:
            ToolError: If tool not found
        """
        tool = self.get(name)
        if not tool:
            error_msg = f"Tool '{name}' not found"
            log_error_with_alert(
                message=error_msg,
                metadata={"tool_name": name, "available_tools": self.list()},
            )
            raise ToolError(error_msg)
        return tool.run(inputs)

