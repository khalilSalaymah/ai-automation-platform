"""URL crawler for syncing web content."""

import uuid
from typing import List, Optional
from urllib.parse import urljoin, urlparse
from loguru import logger
import httpx

from .database import get_session
from .knowledge_models import Document, DocumentSource, DocumentStatus
from .knowledge_service import KnowledgeBaseService
from .errors import AgentFrameworkError


class URLCrawler:
    """Crawler for fetching and processing web content."""

    def __init__(self, max_depth: int = 2, max_pages: int = 50):
        """
        Initialize URL crawler.

        Args:
            max_depth: Maximum crawl depth
            max_pages: Maximum number of pages to crawl
        """
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.knowledge_service = KnowledgeBaseService()
        self.visited_urls = set()

    def _fetch_url_content(self, url: str) -> tuple[str, str]:
        """
        Fetch content from URL.

        Args:
            url: URL to fetch

        Returns:
            Tuple of (title, text_content)
        """
        try:
            response = httpx.get(url, timeout=30.0, follow_redirects=True)
            response.raise_for_status()

            # Simple HTML parsing (can be enhanced with BeautifulSoup)
            content = response.text

            # Extract title
            title_start = content.find("<title>")
            title_end = content.find("</title>")
            title = (
                content[title_start + 7 : title_end].strip() if title_start > -1 else "Untitled"
            )

            # Simple text extraction (remove HTML tags)
            import re

            # Remove script and style tags
            content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL | re.IGNORECASE)
            content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL | re.IGNORECASE)

            # Remove HTML tags
            text = re.sub(r"<[^>]+>", " ", content)

            # Clean up whitespace
            text = re.sub(r"\s+", " ", text).strip()

            return title, text

        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
            raise AgentFrameworkError(f"Failed to fetch URL: {e}") from e

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract links from HTML.

        Args:
            html: HTML content
            base_url: Base URL for resolving relative links

        Returns:
            List of absolute URLs
        """
        import re

        links = []
        pattern = r'href=["\']([^"\']+)["\']'
        matches = re.findall(pattern, html, re.IGNORECASE)

        for match in matches:
            absolute_url = urljoin(base_url, match)
            parsed = urlparse(absolute_url)

            # Only include same-domain links
            base_parsed = urlparse(base_url)
            if parsed.netloc == base_parsed.netloc:
                links.append(absolute_url)

        return links

    def sync_url(
        self,
        url: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        crawl: bool = False,
    ) -> str:
        """
        Sync a single URL or crawl a website.

        Args:
            url: URL to sync
            name: Optional document name
            user_id: User ID
            org_id: Organization ID
            crawl: Whether to crawl linked pages

        Returns:
            Document ID
        """
        if crawl:
            return self._crawl_website(url, name, user_id, org_id)
        else:
            return self._sync_single_url(url, name, user_id, org_id)

    def _sync_single_url(
        self,
        url: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
    ) -> str:
        """Sync a single URL."""
        try:
            title, text = self._fetch_url_content(url)

            # Create document record
            doc_id = str(uuid.uuid4())
            with next(get_session()) as session:
                document = Document(
                    id=doc_id,
                    name=name or title,
                    source=DocumentSource.URL,
                    source_url=url,
                    file_type="text/html",
                    status=DocumentStatus.PENDING,
                    user_id=user_id,
                    org_id=org_id,
                    metadata={"url": url, "title": title},
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

            logger.info(f"Synced URL {url} as document {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Error syncing URL {url}: {e}")
            raise AgentFrameworkError(f"Failed to sync URL: {e}") from e

    def _crawl_website(
        self,
        start_url: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
    ) -> str:
        """Crawl a website starting from a URL."""
        self.visited_urls.clear()
        urls_to_visit = [(start_url, 0)]  # (url, depth)
        document_ids = []

        while urls_to_visit and len(self.visited_urls) < self.max_pages:
            url, depth = urls_to_visit.pop(0)

            if url in self.visited_urls or depth > self.max_depth:
                continue

            self.visited_urls.add(url)

            try:
                response = httpx.get(url, timeout=30.0, follow_redirects=True)
                response.raise_for_status()

                title, text = self._fetch_url_content(url)

                # Create document for this page
                doc_id = str(uuid.uuid4())
                with next(get_session()) as session:
                    document = Document(
                        id=doc_id,
                        name=f"{title or 'Page'} ({url})",
                        source=DocumentSource.URL,
                        source_url=url,
                        file_type="text/html",
                        status=DocumentStatus.PENDING,
                        user_id=user_id,
                        org_id=org_id,
                        metadata={"url": url, "title": title, "crawl_depth": depth},
                    )
                    session.add(document)
                    session.commit()

                # Store text content temporarily
                import tempfile

                temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt")
                temp_file.write(text)
                temp_file.close()

                with next(get_session()) as session:
                    document = session.get(Document, doc_id)
                    document.file_path = temp_file.name
                    session.commit()

                document_ids.append(doc_id)

                # Extract links if not at max depth
                if depth < self.max_depth:
                    links = self._extract_links(response.text, url)
                    for link in links:
                        if link not in self.visited_urls:
                            urls_to_visit.append((link, depth + 1))

                logger.info(f"Crawled URL {url} (depth {depth})")

            except Exception as e:
                logger.warning(f"Error crawling URL {url}: {e}")
                continue

        logger.info(f"Crawled {len(document_ids)} pages from {start_url}")
        return document_ids[0] if document_ids else None  # Return first document ID
