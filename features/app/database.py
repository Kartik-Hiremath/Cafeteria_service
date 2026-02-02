from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load .env from project root (parent of features/) or current dir
load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from app.config import DATABASE_URL  # noqa: E402

if str(DATABASE_URL).startswith("postgres"):
    # Postgres connection with proper isolation level for transactions
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        isolation_level="READ COMMITTED"  # Standard isolation level
    )
else:
    # SQLite connection (for local dev without Postgres)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        isolation_level="SERIALIZABLE"  # SQLite default, prevents race conditions
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# Dependency for routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
