"""Database connection and session management"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from app.config import settings
from app.models.base import Base
from app.models.models import *  # noqa: F401, F403

# Create database engine with connection pooling
connect_args = {}
engine_kwargs = {
    "echo": settings.DEBUG,
    "connect_args": connect_args
}

if "sqlite" in settings.DATABASE_URL:
    # SQLite doesn't support pooling parameters
    # Allow SQLite to be used across threads for testing
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL and other databases support pooling
    engine_kwargs["poolclass"] = QueuePool
    engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
    
    if "postgresql" in settings.DATABASE_URL or "postgres" in settings.DATABASE_URL:
        connect_args = {
            "connect_timeout": 10,
            "application_name": "gra_api",
        }
        engine_kwargs["connect_args"] = connect_args

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


def get_db() -> Session:
    """Get database session for dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database by creating all tables"""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all tables (for testing/cleanup)"""
    Base.metadata.drop_all(bind=engine)


# Enable foreign key constraints for SQLite (if used)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints for SQLite"""
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
