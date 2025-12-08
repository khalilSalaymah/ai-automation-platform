"""Scraper agent."""

from core.agents import ToolExecutionAgent
from ..tools.scraper_tools import ScraperTools


class ScraperAgent(ToolExecutionAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tools = ScraperTools()
        tools.register_all(self.tools)

    def get_system_prompt(self) -> str:
        return "You are a web scraping agent. Extract and summarize web content."

