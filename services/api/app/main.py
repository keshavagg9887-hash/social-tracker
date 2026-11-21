"""Social Empowerment Platform - Main FastAPI Application [M3].

Orchestrates:
- REST API routers for Auth, Users, Incidents, Assignments, Analytics, Devices, and AI Ingestion
- Real-time WebSockets for Handler Dashboard live stream
- Database initialization and default user seeding
- Background Redis Stream Consumer for AI Detection Candidates
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .ai_detections.router import router as ai_detections_router
from .analytics.router import router as analytics_router
from .assignments.router import router as assignments_router
from .auth.router import router as auth_router
from .config import settings
from .database.session import init_db
from .devices.router import router as devices_router
from .incidents.consumer import redis_consumer
from .incidents.router import router as incidents_router
from .notifications.router import router as notifications_router
from .streams.router import router as streams_router
from .users.router import router as users_router
from .websocket.router import router as websocket_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sep-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application Lifespan: DB migration/seeding on startup and background consumer loop."""
    logger.info("Initializing Social Empowerment Platform API...")
    # 1. Initialize database schema & seed default accounts
    await init_db()

    # 2. Start background Redis consumer for AI detection events
    try:
        await redis_consumer.start()
    except Exception as e:
        logger.warning(f"Could not start background Redis consumer: {e}")

    yield

    # Shutdown: stop background consumer
    logger.info("Shutting down Social Empowerment Platform API...")
    await redis_consumer.stop()


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for device management, AI detections, incidents, and streaming.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Feature Routers under /api
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(users_router, prefix=settings.API_PREFIX)
app.include_router(incidents_router, prefix=settings.API_PREFIX)
app.include_router(assignments_router, prefix=settings.API_PREFIX)
app.include_router(notifications_router, prefix=settings.API_PREFIX)
app.include_router(analytics_router, prefix=settings.API_PREFIX)
app.include_router(ai_detections_router, prefix=settings.API_PREFIX)
app.include_router(devices_router, prefix=settings.API_PREFIX)
app.include_router(streams_router, prefix=settings.API_PREFIX)

# Mount WebSocket Router
app.include_router(websocket_router)


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Service health and component status check."""
    return {
        "status": "healthy",
        "service": "social-empowerment-api",
        "version": settings.APP_VERSION,
        "modules": {
            "auth": "ready",
            "incidents": "ready",
            "assignments": "ready",
            "notifications": "ready",
            "analytics": "ready",
            "websocket": "ready",
            "ai_detections": "ready",
        },
    }
