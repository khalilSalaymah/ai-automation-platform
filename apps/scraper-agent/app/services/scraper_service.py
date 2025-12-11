"""Scraper service."""

from core import LLM
from ..agents.scraper_agent import ScraperAgent
from ..config import settings


class ScraperService:
    def __init__(self):
        # LLM will auto-detect provider from LLM_PROVIDER env var
        # For scraper, use Mixtral model for better extraction accuracy
        # Set LLM_PROVIDER=groq and GROQ_API_KEY
        self.llm = LLM(model="mixtral-8x7b-32768")
        self.agent = ScraperAgent(name="scraper-agent", llm=self.llm)

    async def scrape_url(self, url: str):
        result = self.agent.act({"url": url})
        return {"content": result.get("content", ""), "summary": result.get("summary", "")}

