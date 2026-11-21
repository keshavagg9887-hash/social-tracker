"""Application Configuration & Environment Settings [M3].

Central configuration management supporting PostgreSQL, Redis, JWT authentication,
and streaming thresholds.
"""

import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings loaded from environment variables."""

    # Service Info
    APP_NAME: str = "Social Empowerment Platform API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/social_empowerment_db",
        description="Async SQLAlchemy database connection string",
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for streams and pub/sub",
    )
    REDIS_STREAM_AI_EVENTS: str = "ai:events"
    REDIS_STREAM_NOTIFICATIONS: str = "sep:notifications"
    REDIS_CONSUMER_GROUP: str = "sep_incident_engine_group"
    REDIS_CONSUMER_NAME: str = "engine_worker_1"

    # Authentication & JWT
    SECRET_KEY: str = Field(
        default="change-this-to-a-super-secret-key-in-production-sep-2026",
        description="Secret key for JWT token encoding/decoding",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Incident Engine Deduplication & Correlation
    INCIDENT_DEDUPLICATION_WINDOW_SECONDS: int = 600  # 10 minutes
    MIN_DETECTION_CONFIDENCE: float = 0.50

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "*",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
