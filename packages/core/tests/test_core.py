"""Tests for core package."""

import pytest
from core import LLM, RedisSessionMemory, ToolRegistry, Tool, FunctionTool


def test_tool_registry():
    """Test tool registry."""
    registry = ToolRegistry()

    def test_func(x: int, y: int) -> int:
        return x + y

    registry.register_function(
        "add",
        "Add two numbers",
        test_func,
        {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
            },
            "required": ["x", "y"],
        },
    )

    assert "add" in registry.list()
    result = registry.execute("add", {"x": 2, "y": 3})
    assert result["result"] == 5
    assert result["success"] is True


def test_tool_registry_not_found():
    """Test tool registry error handling."""
    registry = ToolRegistry()
    with pytest.raises(Exception):
        registry.execute("nonexistent", {})

