"""FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from core.logger import logger
from core import auth_router, init_db

load_dotenv()

from .routers.scraper_router import router as scraper_router

app = FastAPI(title="Scraper Agent API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Include auth router
app.include_router(auth_router, prefix="/api")

# Include app routers
app.include_router(scraper_router, prefix="/api/scraper", tags=["scraper"])


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()
    logger.info("Scraper Agent API starting up")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "scraper-agent"}

