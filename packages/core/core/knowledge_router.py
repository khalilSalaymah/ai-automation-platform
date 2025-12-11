"""Knowledge base API router."""

from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Query
from sqlmodel import Session, select

from .database import get_session
from .dependencies import get_current_active_user, get_user_org_id
from .models import User
from .knowledge_models import (
    DocumentCreate,
    DocumentResponse,
    DocumentSearchRequest,
    DocumentSearchResult,
    AgentDocumentLink,
    AgentDocumentResponse,
)
from .knowledge_service import KnowledgeBaseService
from .url_crawler import URLCrawler
from .notion_importer import NotionImporter
from .task_queue import TaskQueue
from .config import get_settings
from .errors import AgentFrameworkError

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])
settings = get_settings()


def process_document_task(document_id: str) -> dict:
    """
    Background task for processing document.
    This function is called by RQ worker.
    """
    from .knowledge_service import KnowledgeBaseService

    service = KnowledgeBaseService()
    try:
        service.process_document(document_id)
        return {"status": "success", "document_id": document_id}
    except Exception as e:
        from .logger import logger

        logger.error(f"Error processing document {document_id}: {e}")
        raise


@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    org_id: Optional[str] = Depends(get_user_org_id),
    background_tasks: BackgroundTasks = None,
):
    """Upload a document for processing."""
    try:
        service = KnowledgeBaseService()
        content = await file.read()

        doc_id = service.upload_document(
            name=file.filename or "Untitled",
            file_content=content,
            file_type=file.content_type or "",
            user_id=current_user.id,
            org_id=org_id,
        )

        # Enqueue processing task
        task_queue = TaskQueue(queue_name="knowledge")
        task_queue.enqueue(
            func=process_document_task,
            agent_name="knowledge-base",
            task_name="process_document",
            function_path="core.knowledge_router:process_document_task",
            args=(doc_id,),
        )

        # Get document
        with next(get_session()) as session:
            from .knowledge_models import Document

            document = session.get(Document, doc_id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")

            return DocumentResponse(
                id=document.id,
                name=document.name,
                source=document.source,
                source_url=document.source_url,
                file_type=document.file_type,
                file_size=document.file_size,
                status=document.status,
                total_chunks=document.total_chunks,
                processed_chunks=document.processed_chunks,
                error_message=document.error_message,
                metadata=document.metadata,
                created_at=document.created_at,
                updated_at=document.updated_at,
            )

    except AgentFrameworkError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/url", response_model=DocumentResponse)
async def sync_url(
    url: str = Query(...),
    name: Optional[str] = Query(None),
    crawl: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    org_id: Optional[str] = Depends(get_user_org_id),
):
    """Sync a URL or crawl a website."""
    try:
        crawler = URLCrawler()
        doc_id = crawler.sync_url(
            url=url, name=name, user_id=current_user.id, org_id=org_id, crawl=crawl
        )

        # Enqueue processing task
        task_queue = TaskQueue(queue_name="knowledge")
        task_queue.enqueue(
            func=process_document_task,
            agent_name="knowledge-base",
            task_name="process_document",
            function_path="core.knowledge_router:process_document_task",
            args=(doc_id,),
        )

        # Get document
        with next(get_session()) as session:
            from .knowledge_models import Document

            document = session.get(Document, doc_id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")

            return DocumentResponse(
                id=document.id,
                name=document.name,
                source=document.source,
                source_url=document.source_url,
                file_type=document.file_type,
                file_size=document.file_size,
                status=document.status,
                total_chunks=document.total_chunks,
                processed_chunks=document.processed_chunks,
                error_message=document.error_message,
                metadata=document.metadata,
                created_at=document.created_at,
                updated_at=document.updated_at,
            )

    except AgentFrameworkError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/notion", response_model=DocumentResponse)
async def import_notion_page(
    page_id: str = Query(...),
    name: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    org_id: Optional[str] = Depends(get_user_org_id),
):
    """Import a Notion page."""
    try:
        if not settings.notion_api_key:
            raise HTTPException(status_code=400, detail="Notion API key not configured")

        importer = NotionImporter(api_key=settings.notion_api_key)
        doc_id = importer.import_page(
            page_id=page_id, name=name, user_id=current_user.id, org_id=org_id
        )

        # Enqueue processing task
        task_queue = TaskQueue(queue_name="knowledge")
        task_queue.enqueue(
            func=process_document_task,
            agent_name="knowledge-base",
            task_name="process_document",
            function_path="core.knowledge_router:process_document_task",
            args=(doc_id,),
        )

        # Get document
        with next(get_session()) as session:
            from .knowledge_models import Document

            document = session.get(Document, doc_id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")

            return DocumentResponse(
                id=document.id,
                name=document.name,
                source=document.source,
                source_url=document.source_url,
                file_type=document.file_type,
                file_size=document.file_size,
                status=document.status,
                total_chunks=document.total_chunks,
                processed_chunks=document.processed_chunks,
                error_message=document.error_message,
                metadata=document.metadata,
                created_at=document.created_at,
                updated_at=document.updated_at,
            )

    except AgentFrameworkError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_active_user),
    org_id: Optional[str] = Depends(get_user_org_id),
    session: Session = Depends(get_session),
):
    """List all documents."""
    from .knowledge_models import Document

    query = select(Document)
    if org_id:
        query = query.where(Document.org_id == org_id)

    documents = list(session.exec(query).all())
    return [
        DocumentResponse(
            id=doc.id,
            name=doc.name,
            source=doc.source,
            source_url=doc.source_url,
            file_type=doc.file_type,
            file_size=doc.file_size,
            status=doc.status,
            total_chunks=doc.total_chunks,
            processed_chunks=doc.processed_chunks,
            error_message=doc.error_message,
            metadata=doc.metadata,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
        for doc in documents
    ]


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    org_id: Optional[str] = Depends(get_user_org_id),
    session: Session = Depends(get_session),
):
    """Get a document by ID."""
    from .knowledge_models import Document

    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if org_id and document.org_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return DocumentResponse(
        id=document.id,
        name=document.name,
        source=document.source,
        source_url=document.source_url,
        file_type=document.file_type,
        file_size=document.file_size,
        status=document.status,
        total_chunks=document.total_chunks,
        processed_chunks=document.processed_chunks,
        error_message=document.error_message,
        metadata=document.metadata,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    org_id: Optional[str] = Depends(get_user_org_id),
):
    """Delete a document."""
    try:
        service = KnowledgeBaseService()
        service.delete_document(document_id, org_id=org_id)
        return {"message": "Document deleted successfully"}
    except AgentFrameworkError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/search", response_model=List[DocumentSearchResult])
async def search_documents(
    request: DocumentSearchRequest,
    current_user: User = Depends(get_current_active_user),
    org_id: Optional[str] = Depends(get_user_org_id),
):
    """Search documents using semantic search."""
    try:
        service = KnowledgeBaseService()
        results = service.search_documents(request, org_id=org_id)
        return results
    except AgentFrameworkError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/{agent_name}/documents")
async def link_documents_to_agent(
    agent_name: str,
    link: AgentDocumentLink,
    current_user: User = Depends(get_current_active_user),
    org_id: Optional[str] = Depends(get_user_org_id),
):
    """Link documents to an agent."""
    try:
        service = KnowledgeBaseService()
        service.link_documents_to_agent(agent_name, link.document_ids, org_id=org_id)
        return {"message": f"Linked {len(link.document_ids)} documents to agent {agent_name}"}
    except AgentFrameworkError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_name}/documents", response_model=AgentDocumentResponse)
async def get_agent_documents(
    agent_name: str,
    current_user: User = Depends(get_current_active_user),
    org_id: Optional[str] = Depends(get_user_org_id),
):
    """Get documents linked to an agent."""
    try:
        service = KnowledgeBaseService()
        documents = service.get_agent_documents(agent_name, org_id=org_id)

        return AgentDocumentResponse(
            agent_name=agent_name,
            documents=[
                DocumentResponse(
                    id=doc.id,
                    name=doc.name,
                    source=doc.source,
                    source_url=doc.source_url,
                    file_type=doc.file_type,
                    file_size=doc.file_size,
                    status=doc.status,
                    total_chunks=doc.total_chunks,
                    processed_chunks=doc.processed_chunks,
                    error_message=doc.error_message,
                    metadata=doc.metadata,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                )
                for doc in documents
            ],
        )
    except AgentFrameworkError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
