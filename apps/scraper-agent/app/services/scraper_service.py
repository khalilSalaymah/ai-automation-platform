"""Scraper service."""

from core import LLM
from ..agents.scraper_agent import ScraperAgent
from ..config import settings


class ScraperService:
    def __init__(self):
        self.llm = LLM(api_key=settings.openai_api_key, model=settings.openai_model)
        self.agent = ScraperAgent(name="scraper-agent", llm=self.llm)

    async def scrape_url(self, url: str):
        result = self.agent.act({"url": url})
        return {"content": result.get("content", ""), "summary": result.get("summary", "")}

