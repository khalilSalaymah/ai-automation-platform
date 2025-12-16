"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
from core.logger import logger
from core import auth_router, init_db, scheduler_router, TaskScheduler

load_dotenv()

from .routers.support_router import router as support_router
from .config import settings

app = FastAPI(title="Support Bot API", description="AI support bot", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router, prefix="/api")

# Include scheduler router
app.include_router(scheduler_router, prefix="/api/scheduler", tags=["scheduler"])

# Include app routers
# Expose support-bot APIs under /api to match other apps and keep
# the external contract simple:
# - POST /api/chat
# - POST /api/tickets
# - GET  /api/tickets/{ticket_id}
app.include_router(support_router, prefix="/api", tags=["support"])


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()
    
    # Initialize scheduler and load tasks
    scheduler = TaskScheduler()
    yaml_path = Path(__file__).parent.parent / "tasks.yaml"
    if yaml_path.exists():
        tasks = scheduler.load_tasks_from_yaml(str(yaml_path), agent_name="support-bot")
        for task in tasks:
            scheduler.register_task(task)
        logger.info(f"Loaded {len(tasks)} scheduled tasks for support-bot")
    
    logger.info("Support Bot API starting up")


@logger.catch
@app.get("/health")
async def health():
    return {"status": "ok", "service": "support-bot"}

