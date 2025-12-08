"""Scraper tools."""

import requests
from bs4 import BeautifulSoup
from core.tools import ToolRegistry


class ScraperTools:
    def register_all(self, registry: ToolRegistry):
        registry.register_function("scrape_webpage", "Scrape a webpage", self.scrape_webpage, {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        })

    @staticmethod
    def scrape_webpage(url: str) -> dict:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            return {"text": soup.get_text(), "title": soup.title.string if soup.title else ""}
        except Exception as e:
            return {"error": str(e)}

