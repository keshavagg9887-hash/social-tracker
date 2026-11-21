"""Database Session & Engine Management [M3].

Provides async SQLAlchemy engine, async session factory, transaction helpers,
and database bootstrap seeding.
"""

import logging
from typing import AsyncGenerator
from ..config import settings
from .models import Base, User

logger = logging.getLogger(__name__)

try:
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    db_url = settings.DATABASE_URL
    connect_args = {}

    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_async_engine(
        db_url,
        echo=settings.DEBUG,
        future=True,
        connect_args=connect_args,
    )

    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
except ImportError:
    AsyncSession = None
    async_sessionmaker = None
    create_async_engine = None
    engine = None
    AsyncSessionLocal = None


async def get_db() -> AsyncGenerator:
    """Dependency that yields an async database session per request."""
    if not AsyncSessionLocal:
        raise RuntimeError("SQLAlchemy is not installed in this environment.")
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create tables if they don't exist and seed default accounts."""
    if not engine or not AsyncSessionLocal:
        logger.warning("Database engine not available (SQLAlchemy missing). Skipping schema initialization.")
        return

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized successfully.")

        # Seed initial admin and handler accounts
        async with AsyncSessionLocal() as session:
            from ..auth.security import get_password_hash
            from sqlalchemy import select

            result = await session.execute(select(User).where(User.email == "admin@socialtracker.org"))
            existing_admin = result.scalar_one_or_none()

            if not existing_admin:
                admin_user = User(
                    email="admin@socialtracker.org",
                    hashed_password=get_password_hash("admin123"),
                    full_name="System Administrator",
                    role="admin",
                    is_active=True,
                )
                session.add(admin_user)
                logger.info("Default administrator seeded: admin@socialtracker.org")

            result_handler = await session.execute(select(User).where(User.email == "handler@socialtracker.org"))
            existing_handler = result_handler.scalar_one_or_none()

            if not existing_handler:
                handler_user = User(
                    email="handler@socialtracker.org",
                    hashed_password=get_password_hash("handler123"),
                    full_name="Emergency Incident Handler",
                    role="handler",
                    is_active=True,
                )
                session.add(handler_user)
                logger.info("Default incident handler seeded: handler@socialtracker.org")

            await session.commit()
    except Exception as e:
        logger.warning(f"Database initialization warning (schema may already exist or DB offline): {e}")
