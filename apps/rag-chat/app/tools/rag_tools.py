"""RAG-specific tools."""

from core.tools import ToolRegistry


class RAGTools:
    """RAG processing tools."""

    def register_all(self, registry: ToolRegistry):
        """Register all RAG tools."""
        registry.register_function(
            "search_documents",
            "Search for relevant documents",
            self.search_documents,
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
        )

    @staticmethod
    def search_documents(query: str) -> dict:
        """Search documents."""
        return {"results": [], "count": 0}

