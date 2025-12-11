"""Support service."""

from core import LLM, RedisSessionMemory
from ..agents.support_agent import SupportAgent
from ..config import settings


class SupportService:
    def __init__(self):
        # LLM will auto-detect provider from LLM_PROVIDER env var
        # For Groq apps, set LLM_PROVIDER=groq and GROQ_API_KEY
        self.llm = LLM(model="llama3-8b-8192")
        self.memory = RedisSessionMemory(url=settings.redis_url)
        self.agent = SupportAgent(name="support-agent", llm=self.llm, memory=self.memory)

    async def handle_message(self, message: str, session_id: str):
        result = self.agent.act({"query": message, "session_id": session_id})
        return {"response": result.get("response", "")}

