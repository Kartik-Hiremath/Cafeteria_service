"""Pytest configuration. Ensures database is initialized before tests."""
import pytest

from app.database import Base, engine
from app import models  # noqa: F401 - register models with Base


@pytest.fixture(autouse=True)
def ensure_db():
    """Create tables before each test (some tests use db_session which drops_all)."""
    Base.metadata.create_all(bind=engine)
    yield
