"""Support agent."""

from core.agents import ToolExecutionAgent


class SupportAgent(ToolExecutionAgent):
    def get_system_prompt(self) -> str:
        # Optimized for Groq: structured, clear instructions work best
        return """Support agent. Rules:
- Friendly, professional tone
- Solve problems quickly
- Use tools when needed
- Format: Clear, concise responses"""

