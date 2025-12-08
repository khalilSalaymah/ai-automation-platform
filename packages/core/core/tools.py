"""Tool registry and standardized tool interface."""

from typing import Callable, Dict, Any, List, Optional
from abc import ABC, abstractmethod
from loguru import logger

from .errors import ToolError


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
        """Execute wrapped function."""
        try:
            result = self.func(**inputs)
            return {"result": result, "success": True}
        except Exception as e:
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
        Execute a tool by name.

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
            raise ToolError(f"Tool '{name}' not found")
        return tool.run(inputs)

