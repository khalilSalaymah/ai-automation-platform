"""AIOps service."""

from core import LLM
from ..agents.aiops_agent import AiOpsAgent
from ..config import settings


class AiOpsService:
    def __init__(self):
        self.llm = LLM(api_key=settings.openai_api_key, model=settings.openai_model)
        self.agent = AiOpsAgent(name="aiops-agent", llm=self.llm)

    async def analyze(self, query: str, metrics: dict):
        result = self.agent.act({"query": query, "metrics": metrics})
        return {"analysis": result.get("response", ""), "recommendations": result.get("recommendations", [])}

