import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lifeos.db")

# connect_args only needed for SQLite (thread safety)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Import all models so Base knows about them before creating tables
    from backend.memory import schema  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _migrate()


def _migrate():
    """Apply additive schema changes that create_all won't handle on existing tables."""
    from sqlalchemy import text
    with engine.connect() as conn:
        # emails.account — added when multi-account Gmail support was introduced
        try:
            conn.execute(text("ALTER TABLE emails ADD COLUMN account VARCHAR(50) DEFAULT 'unknown'"))
            conn.commit()
        except Exception:
            pass  # column already exists
