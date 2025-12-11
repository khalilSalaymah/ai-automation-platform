"""AIOps agent."""

from core.agents import ToolExecutionAgent


class AiOpsAgent(ToolExecutionAgent):
    def get_system_prompt(self) -> str:
        # Optimized for Groq: concise, direct prompts work better
        return "AIOps agent. Analyze metrics. Provide insights and recommendations. Be concise."

