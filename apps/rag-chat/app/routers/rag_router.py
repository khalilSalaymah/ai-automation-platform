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
        service = RAGService()
        result = await service.chat(request.message, request.session_id)
        return result
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload document for indexing."""
    try:
        service = RAGService()
        content = await file.read()
        doc_id = await service.index_document(file.filename, content)
        return {"document_id": doc_id, "filename": file.filename}
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """List indexed documents."""
    try:
        service = RAGService()
        documents = await service.list_documents()
        return documents
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

