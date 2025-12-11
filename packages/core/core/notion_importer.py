"""Notion API importer for syncing Notion pages."""

import uuid
from typing import List, Optional, Dict, Any
from loguru import logger
import httpx

from .database import get_session
from .knowledge_models import Document, DocumentSource, DocumentStatus
from .knowledge_service import KnowledgeBaseService
from .errors import AgentFrameworkError


class NotionImporter:
    """Importer for Notion pages and databases."""

    def __init__(self, api_key: str):
        """
        Initialize Notion importer.

        Args:
            api_key: Notion API key
        """
        self.api_key = api_key
        self.base_url = "https://api.notion.com/v1"
        self.knowledge_service = KnowledgeBaseService()
        self.client = httpx.Client(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def _get_page_content(self, page_id: str) -> tuple[str, str]:
        """
        Get page content from Notion.

        Args:
            page_id: Notion page ID

        Returns:
            Tuple of (title, text_content)
        """
        try:
            # Get page
            response = self.client.get(f"{self.base_url}/pages/{page_id}")
            response.raise_for_status()
            page_data = response.json()

            # Extract title
            title = "Untitled"
            properties = page_data.get("properties", {})
            for prop_name, prop_data in properties.items():
                if prop_data.get("type") == "title" and prop_data.get("title"):
                    title = " ".join([text.get("plain_text", "") for text in prop_data["title"]])
                    break

            # Get page blocks
            blocks_response = self.client.get(f"{self.base_url}/blocks/{page_id}/children")
            blocks_response.raise_for_status()
            blocks = blocks_response.json().get("results", [])

            # Extract text from blocks
            text_parts = []
            for block in blocks:
                block_type = block.get("type")
                block_data = block.get(block_type, {})

                if block_type == "paragraph":
                    rich_text = block_data.get("rich_text", [])
                    text = " ".join([t.get("plain_text", "") for t in rich_text])
                    if text:
                        text_parts.append(text)

                elif block_type == "heading_1":
                    rich_text = block_data.get("rich_text", [])
                    text = " ".join([t.get("plain_text", "") for t in rich_text])
                    if text:
                        text_parts.append(f"# {text}")

                elif block_type == "heading_2":
                    rich_text = block_data.get("rich_text", [])
                    text = " ".join([t.get("plain_text", "") for t in rich_text])
                    if text:
                        text_parts.append(f"## {text}")

                elif block_type == "heading_3":
                    rich_text = block_data.get("rich_text", [])
                    text = " ".join([t.get("plain_text", "") for t in rich_text])
                    if text:
                        text_parts.append(f"### {text}")

                elif block_type == "bulleted_list_item":
                    rich_text = block_data.get("rich_text", [])
                    text = " ".join([t.get("plain_text", "") for t in rich_text])
                    if text:
                        text_parts.append(f"- {text}")

                elif block_type == "numbered_list_item":
                    rich_text = block_data.get("rich_text", [])
                    text = " ".join([t.get("plain_text", "") for t in rich_text])
                    if text:
                        text_parts.append(f"1. {text}")

                elif block_type == "code":
                    rich_text = block_data.get("rich_text", [])
                    text = " ".join([t.get("plain_text", "") for t in rich_text])
                    if text:
                        text_parts.append(f"```\n{text}\n```")

            text_content = "\n\n".join(text_parts)
            return title, text_content

        except Exception as e:
            logger.error(f"Error fetching Notion page {page_id}: {e}")
            raise AgentFrameworkError(f"Failed to fetch Notion page: {e}") from e

    def _search_pages(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for pages in Notion.

        Args:
            query: Optional search query

        Returns:
            List of page objects
        """
        try:
            payload = {"filter": {"property": "object", "value": "page"}}
            if query:
                payload["query"] = query

            response = self.client.post(f"{self.base_url}/search", json=payload)
            response.raise_for_status()
            return response.json().get("results", [])

        except Exception as e:
            logger.error(f"Error searching Notion pages: {e}")
            raise AgentFrameworkError(f"Failed to search Notion pages: {e}") from e

    def import_page(
        self,
        page_id: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
    ) -> str:
        """
        Import a single Notion page.

        Args:
            page_id: Notion page ID
            name: Optional document name
            user_id: User ID
            org_id: Organization ID

        Returns:
            Document ID
        """
        try:
            title, text = self._get_page_content(page_id)

            # Create document record
            doc_id = str(uuid.uuid4())
            notion_url = f"https://www.notion.so/{page_id.replace('-', '')}"

            with next(get_session()) as session:
                document = Document(
                    id=doc_id,
                    name=name or title,
                    source=DocumentSource.NOTION,
                    source_url=notion_url,
                    file_type="text/plain",
                    status=DocumentStatus.PENDING,
                    user_id=user_id,
                    org_id=org_id,
                    metadata={"notion_page_id": page_id, "title": title},
                )
                session.add(document)
                session.commit()

            # Store text content temporarily for processing
            import tempfile

            temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt")
            temp_file.write(text)
            temp_file.close()

            # Update document with file path for processing
            with next(get_session()) as session:
                document = session.get(Document, doc_id)
                document.file_path = temp_file.name
                session.commit()

            logger.info(f"Imported Notion page {page_id} as document {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Error importing Notion page {page_id}: {e}")
            raise AgentFrameworkError(f"Failed to import Notion page: {e}") from e

    def import_database(
        self,
        database_id: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
    ) -> List[str]:
        """
        Import all pages from a Notion database.

        Args:
            database_id: Notion database ID
            name: Optional prefix for document names
            user_id: User ID
            org_id: Organization ID

        Returns:
            List of document IDs
        """
        try:
            # Query database for pages
            response = self.client.post(
                f"{self.base_url}/databases/{database_id}/query", json={}
            )
            response.raise_for_status()
            pages = response.json().get("results", [])

            document_ids = []

            for page in pages:
                page_id = page.get("id")
                if not page_id:
                    continue

                try:
                    doc_id = self.import_page(
                        page_id=page_id,
                        name=f"{name or 'Page'} - {page_id[:8]}" if name else None,
                        user_id=user_id,
                        org_id=org_id,
                    )
                    document_ids.append(doc_id)
                except Exception as e:
                    logger.warning(f"Failed to import page {page_id}: {e}")
                    continue

            logger.info(f"Imported {len(document_ids)} pages from Notion database {database_id}")
            return document_ids

        except Exception as e:
            logger.error(f"Error importing Notion database {database_id}: {e}")
            raise AgentFrameworkError(f"Failed to import Notion database: {e}") from e

    def list_available_pages(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available Notion pages.

        Args:
            query: Optional search query

        Returns:
            List of page metadata
        """
        pages = self._search_pages(query)
        return [
            {
                "id": page.get("id"),
                "title": self._extract_page_title(page),
                "url": page.get("url"),
                "last_edited": page.get("last_edited_time"),
            }
            for page in pages
        ]

    def _extract_page_title(self, page: Dict[str, Any]) -> str:
        """Extract title from page object."""
        properties = page.get("properties", {})
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title" and prop_data.get("title"):
                return " ".join([text.get("plain_text", "") for text in prop_data["title"]])
        return "Untitled"
