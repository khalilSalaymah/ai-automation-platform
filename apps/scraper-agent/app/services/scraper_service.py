"""Scraper service."""

from core import LLM
from ..agents.scraper_agent import ScraperAgent
from ..config import settings


class ScraperService:
    def __init__(self):
        # LLM will auto-detect provider from LLM_PROVIDER env var
        # For Groq apps, set LLM_PROVIDER=groq and GROQ_API_KEY
        self.llm = LLM(model="llama3-8b-8192")
        self.agent = ScraperAgent(name="scraper-agent", llm=self.llm)

    async def scrape_url(self, url: str):
        result = self.agent.act({"url": url})
        return {"content": result.get("content", ""), "summary": result.get("summary", "")}

