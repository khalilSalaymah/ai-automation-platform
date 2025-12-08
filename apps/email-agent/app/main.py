"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from core.logger import logger

load_dotenv()

from .routers.email_router import router as email_router
from .config import settings

app = FastAPI(
    title="Email Agent API",
    description="AI-powered email agent",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(email_router, prefix="/api/email", tags=["email"])


@logger.catch
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "email-agent"}


@app.on_event("startup")
async def startup():
    """Startup event handler."""
    logger.info("Email Agent API starting up")


@app.on_event("shutdown")
async def shutdown():
    """Shutdown event handler."""
    logger.info("Email Agent API shutting down")

