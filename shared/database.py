"""Database utilities for PostgreSQL connections.

This module provides SQLAlchemy session management and connection pooling
utilities shared across all microservices.
"""

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import structlog

logger = structlog.get_logger()

# Base class for SQLAlchemy models
Base = declarative_base()


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(
        self,
        database_url: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_pre_ping: bool = True,
        echo: bool = False
    ):
        """Initialize database manager.

        Args:
            database_url: PostgreSQL connection URL
            pool_size: Number of permanent connections to maintain
            max_overflow: Number of additional connections allowed
            pool_pre_ping: Enable connection health checks
            echo: Enable SQL query logging
        """
        self.database_url = database_url

        # Create engine with connection pooling
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
            echo=echo
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        # Track connection pool metrics
        self._setup_pool_metrics()

        logger.info(
            "database_manager_initialized",
            url=self._sanitize_url(database_url),
            pool_size=pool_size,
            max_overflow=max_overflow
        )

    def _sanitize_url(self, url: str) -> str:
        """Remove credentials from database URL for logging.

        Args:
            url: Database URL

        Returns:
            Sanitized URL without credentials
        """
        if "@" in url:
            return url.split("@", 1)[1]
        return url

    def _setup_pool_metrics(self):
        """Setup event listeners for connection pool metrics."""
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug("database_connection_opened")

        @event.listens_for(self.engine, "close")
        def receive_close(dbapi_conn, connection_record):
            logger.debug("database_connection_closed")

    def create_tables(self):
        """Create all tables defined in models."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("database_tables_created")

    def drop_tables(self):
        """Drop all tables (use with caution)."""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("database_tables_dropped")

    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session (use as context manager or dependency).

        Yields:
            SQLAlchemy session

        Example:
            with db_manager.get_session() as session:
                session.query(Model).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_pool_status(self) -> dict:
        """Get current connection pool status.

        Returns:
            Dictionary with pool statistics
        """
        pool = self.engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total": pool.size() + pool.overflow()
        }

    def close(self):
        """Close all database connections."""
        self.engine.dispose()
        logger.info("database_connections_closed")


def get_database_manager(database_url: str, **kwargs) -> DatabaseManager:
    """Factory function to create a DatabaseManager.

    Args:
        database_url: PostgreSQL connection URL
        **kwargs: Additional arguments for DatabaseManager

    Returns:
        DatabaseManager instance
    """
    return DatabaseManager(database_url, **kwargs)


# Dependency for FastAPI (use with Depends)
def get_db_session(db_manager: DatabaseManager) -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions.

    Args:
        db_manager: DatabaseManager instance

    Yields:
        SQLAlchemy session

    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db_session)):
            return db.query(Item).all()
    """
    yield from db_manager.get_session()
