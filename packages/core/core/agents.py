"""Base agent classes and orchestrator."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from loguru import logger

from .llm import LLM
from .memory import RedisSessionMemory
from .tools import ToolRegistry
from .errors import AgentFrameworkError


class BaseAgent(ABC):
    """Base agent class."""

    def __init__(
        self,
        name: str,
        llm: LLM,
        memory: Optional[RedisSessionMemory] = None,
        tools: Optional[ToolRegistry] = None,
    ):
        """
        Initialize base agent.

        Args:
            name: Agent name
            llm: LLM instance
            memory: Optional memory store
            tools: Optional tool registry
        """
        self.name = name
        self.llm = llm
        self.memory = memory
        self.tools = tools or ToolRegistry()

    @abstractmethod
    def act(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input and return output.

        Args:
            input_data: Input dictionary

        Returns:
            Output dictionary
        """
        raise NotImplementedError

    def get_system_prompt(self) -> str:
        """
        Get system prompt for the agent.

        Returns:
            System prompt string
        """
        return f"You are {self.name}, a helpful AI assistant."


class PlannerAgent(BaseAgent):
    """Agent that plans multi-step tasks."""

    def __init__(self, *args, **kwargs):
        """Initialize planner agent."""
        super().__init__(*args, **kwargs)
        self.max_steps = kwargs.get("max_steps", 10)

    def act(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Plan a sequence of actions.

        Args:
            input_data: Input with 'task' or 'query' key

        Returns:
            Dictionary with 'plan' (list of steps)
        """
        task = input_data.get("task") or input_data.get("query", "")
        session_id = input_data.get("session_id", "default")

        # Build messages
        messages = [{"role": "system", "content": self.get_system_prompt()}]

        if self.memory:
            history = self.memory.get_messages(session_id)
            messages.extend(history)

        messages.append({"role": "user", "content": f"Plan steps to: {task}"})

        try:
            response = self.llm.chat(messages)
            plan_text = response.choices[0].message.content

            # Parse plan (simple extraction - can be enhanced)
            steps = [s.strip() for s in plan_text.split("\n") if s.strip()]

            result = {"plan": steps, "agent": self.name}

            if self.memory:
                self.memory.append_message(session_id, "user", task)
                self.memory.append_message(session_id, "assistant", plan_text)

            return result
        except Exception as e:
            logger.error(f"PlannerAgent error: {e}")
            raise AgentFrameworkError(f"Planning failed: {e}") from e


class ToolExecutionAgent(BaseAgent):
    """Agent that executes tools based on LLM decisions."""

    def act(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tools based on input.

        Args:
            input_data: Input with 'query' or 'action' key

        Returns:
            Dictionary with execution results
        """
        query = input_data.get("query") or input_data.get("action", "")
        session_id = input_data.get("session_id", "default")

        # Build messages
        messages = [{"role": "system", "content": self.get_system_prompt()}]

        if self.memory:
            history = self.memory.get_messages(session_id)
            messages.extend(history)

        messages.append({"role": "user", "content": query})

        # Get function schemas
        functions = self.tools.get_function_schemas() if self.tools else None

        try:
            response = self.llm.chat(messages, functions=functions)

            message = response.choices[0].message

            # Check for function calls
            if hasattr(message, "tool_calls") and message.tool_calls:
                results = []
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_inputs = eval(tool_call.function.arguments)  # Parse JSON string

                    if self.tools:
                        tool_result = self.tools.execute(tool_name, tool_inputs)
                        results.append(
                            {
                                "tool": tool_name,
                                "inputs": tool_inputs,
                                "result": tool_result,
                            }
                        )

                return {"results": results, "agent": self.name}

            # No function calls, return text response
            text_response = message.content
            result = {"response": text_response, "agent": self.name}

            if self.memory:
                self.memory.append_message(session_id, "user", query)
                self.memory.append_message(session_id, "assistant", text_response)

            return result

        except Exception as e:
            logger.error(f"ToolExecutionAgent error: {e}")
            raise AgentFrameworkError(f"Tool execution failed: {e}") from e


class AgentOrchestrator:
    """Orchestrates multiple agents to work together."""

    def __init__(self, agents: List[BaseAgent]):
        """
        Initialize orchestrator.

        Args:
            agents: List of agent instances
        """
        self.agents = {agent.name: agent for agent in agents}

    def route(self, input_data: Dict[str, Any], agent_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Route input to an agent.

        Args:
            input_data: Input dictionary
            agent_name: Optional agent name (auto-routes if not provided)

        Returns:
            Agent output

        Raises:
            AgentFrameworkError: If agent not found
        """
        if agent_name:
            if agent_name not in self.agents:
                raise AgentFrameworkError(f"Agent '{agent_name}' not found")
            agent = self.agents[agent_name]
        else:
            # Auto-route to first agent (can be enhanced with routing logic)
            agent = list(self.agents.values())[0]

        return agent.act(input_data)

    def add_agent(self, agent: BaseAgent):
        """Add an agent to the orchestrator."""
        self.agents[agent.name] = agent
        logger.info(f"Added agent: {agent.name}")

    def list_agents(self) -> List[str]:
        """List all agent names."""
        return list(self.agents.keys())

