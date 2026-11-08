from typing import Generator
from sqlalchemy import create_engine, text
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
    # Explicit 5-second socket timeout and conservative connection pooling for Supabase/Render
    connect_args = {"connect_timeout": 5}
    pool_kwargs = {
        "pool_size": 3,
        "max_overflow": 2,
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
    """Dependency for obtaining a SQLAlchemy session per request.
    
    Guarantees clean transaction rollback upon exceptions and session closure.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_health(timeout_seconds: float = 3.0) -> bool:
    """Verifies active database reachability with a fast bounded query without throwing."""
    try:
        with engine.connect() as conn:
            # Set statement timeout for PostgreSQL to prevent hanging queries
            if not db_url.startswith("sqlite"):
                conn.execute(text(f"SET statement_timeout = {int(timeout_seconds * 1000)}"))
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def init_db() -> None:
    """Create all configured tables if they do not exist.
    
    In development (SQLite), this creates tables automatically.
    In production (PostgreSQL), tables are pre-migrated.
    """
    import backend.models  # noqa: F401
    Base.metadata.create_all(bind=engine)


