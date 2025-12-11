"""Gateway service main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from core.logger import logger
from core import init_db
from .config import get_settings
from .routers import gateway_router
from .middleware import rate_limit, quota, logging
from .services.routing import get_routing_service

load_dotenv()

settings = get_settings()

app = FastAPI(
    title="AI Automation Platform Gateway",
    description="API Gateway for routing requests to agent services",
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

# Add custom middleware (order matters!)
app.middleware("http")(logging.logging_middleware)
app.middleware("http")(rate_limit.rate_limit_middleware)
app.middleware("http")(quota.check_quota_middleware)

# Include routers
app.include_router(gateway_router.router)


@app.on_event("startup")
async def startup():
    """Startup event handler."""
    # Initialize database
    init_db()
    
    # Initialize routing service
    get_routing_service()
    
    logger.info("Gateway service starting up")


@app.on_event("shutdown")
async def shutdown():
    """Shutdown event handler."""
    # Close routing service HTTP client
    routing_service = get_routing_service()
    await routing_service.close()
    
    logger.info("Gateway service shutting down")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=True,
    )
