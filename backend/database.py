from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.config import get_settings

settings = get_settings()

# Normalize database URL (e.g. Supabase postgres:// -> postgresql://)
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Configure connection arguments and pool parameters based on engine type
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    pool_kwargs = {}
else:
    # Explicit 5-second socket timeout and resilient connection pooling for PostgreSQL
    connect_args = {"connect_timeout": 5}
    pool_kwargs = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 10
    }

engine = create_engine(
    db_url,
    connect_args=connect_args,
    **pool_kwargs,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining a SQLAlchemy session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all configured tables if they do not exist."""
    # Import models here to ensure metadata is populated before creation
    import backend.models  # noqa: F401
    Base.metadata.create_all(bind=engine)

