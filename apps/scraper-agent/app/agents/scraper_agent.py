"""Scraper agent."""

from typing import Dict, Any
import json
from core.agents import ToolExecutionAgent
from core.logger import logger
from ..tools.scraper_tools import ScraperTools


class ScraperAgent(ToolExecutionAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tools = ScraperTools()
        tools.register_all(self.tools)

    def get_system_prompt(self) -> str:
        # Optimized for Mixtral: structured extraction instructions
        return """Web scraper. Extract structured data. Output JSON:
{
  "content": "main text",
  "title": "page title",
  "summary": "brief summary",
  "links": ["url1", "url2"],
  "metadata": {"key": "value"}
}"""

    def act(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process scraping request with structured JSON output.
        
        Args:
            input_data: Input with 'url' key
            
        Returns:
            Dictionary with content, summary, title, links, metadata
        """
        url = input_data.get("url", "")
        query = f"Scrape and extract: {url}"
        
        input_data["query"] = query
        result = super().act(input_data)
        
        # Parse JSON from response
        response_text = result.get("response", "")
        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                parsed = json.loads(json_str)
                # Extract structured fields
                result["content"] = parsed.get("content", "")
                result["summary"] = parsed.get("summary", "")
                result["title"] = parsed.get("title", "")
                result["links"] = parsed.get("links", [])
                result["metadata"] = parsed.get("metadata", {})
            else:
                # Fallback: use response as content
                result["content"] = response_text
                result["summary"] = response_text[:200] + "..." if len(response_text) > 200 else response_text
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse JSON from scraper response: {e}")
            # Fallback: use response as content
            result["content"] = response_text
            result["summary"] = response_text[:200] + "..." if len(response_text) > 200 else response_text
        
        return result

