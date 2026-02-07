"""Database configuration for Tracking Service."""

import os
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base
import structlog

logger = structlog.get_logger()

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:demo_password_123@postgresql:5432/tracking_db"
)

# Create database engine
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("database_tables_created", database="tracking_db")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        raise


def get_db() -> Generator[Session, None, None]:
    """Get database session dependency for FastAPI.

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_status() -> str:
    """Check database connectivity.

    Returns:
        Status string ('healthy' or 'unhealthy')
    """
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return "healthy"
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return "unhealthy"
