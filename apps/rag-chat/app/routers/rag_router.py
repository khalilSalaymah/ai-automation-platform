"""RAG API routes."""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from core.logger import logger

from ..services.rag_service import RAGService
from ..models.rag_models import ChatRequest, ChatResponse, DocumentInfo

router = APIRouter()


class ChatRequestModel(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequestModel):
    """Chat with RAG."""
    try:
        logger.info(f"Chat request: message='{request.message[:100]}...', session_id={request.session_id}")
        service = RAGService()
        result = await service.chat(request.message, request.session_id)
        logger.info(f"Chat response generated: {len(result.response)} chars, {len(result.sources)} sources")
        return result
    except Exception as e:
        logger.error(f"Error in chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload document for indexing."""
    try:
        logger.info(f"Received document upload request: {file.filename}")
        service = RAGService()
        content = await file.read()
        logger.info(f"Read {len(content)} bytes from uploaded file")
        doc_id = await service.index_document(file.filename, content)
        logger.info(f"Successfully indexed document {file.filename} with ID: {doc_id}")
        return {"document_id": doc_id, "filename": file.filename}
    except Exception as e:
        logger.error(f"Error uploading document {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """List indexed documents."""
    try:
        logger.info("Received request to list documents")
        service = RAGService()
        documents = await service.list_documents()
        logger.info(f"Returning {len(documents)} documents")
        return documents
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

