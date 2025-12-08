"""AIOps agent."""

from core.agents import ToolExecutionAgent


class AiOpsAgent(ToolExecutionAgent):
    def get_system_prompt(self) -> str:
        return "You are an AIOps agent. Analyze system metrics and provide insights and recommendations."

