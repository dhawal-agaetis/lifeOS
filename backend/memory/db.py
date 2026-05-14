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

        # orders table — rebuilt with richer schema; add new columns to existing installs
        _add_column(conn, "orders", "date_added", "VARCHAR(20)")
        _add_column(conn, "orders", "status", "VARCHAR(100)")
        _add_column(conn, "orders", "subtotal", "NUMERIC(10,2)")
        _add_column(conn, "orders", "vat", "NUMERIC(10,2)")
        _add_column(conn, "orders", "grand_total", "NUMERIC(10,2)")
        _add_column(conn, "orders", "comments", "TEXT")
        _add_column(conn, "orders", "deliver_by", "VARCHAR(255)")
        _add_column(conn, "orders", "is_business_customer", "BOOLEAN DEFAULT 0")
        _add_column(conn, "orders", "source_email", "VARCHAR(50)")


def _add_column(conn, table: str, column: str, col_type: str):
    from sqlalchemy import text
    try:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
        conn.commit()
    except Exception:
        pass  # column already exists
