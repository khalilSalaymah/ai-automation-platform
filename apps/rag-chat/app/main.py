"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from core.logger import logger
from core import auth_router, init_db

load_dotenv()

from .routers.rag_router import router as rag_router
from .config import settings

app = FastAPI(
    title="RAG Chat API",
    description="Retrieval-Augmented Generation chat",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router, prefix="/api")

# Include app routers
app.include_router(rag_router, prefix="/api", tags=["rag"])


@logger.catch
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "rag-chat"}


@app.on_event("startup")
async def startup():
    """Startup event handler."""
    init_db()
    logger.info("RAG Chat API starting up")


@app.on_event("shutdown")
async def shutdown():
    """Shutdown event handler."""
    logger.info("RAG Chat API shutting down")

