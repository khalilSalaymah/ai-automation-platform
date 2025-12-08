"""Support agent."""

from core.agents import ToolExecutionAgent


class SupportAgent(ToolExecutionAgent):
    def get_system_prompt(self) -> str:
        return "You are a helpful customer support agent. Be friendly, professional, and solution-oriented."

