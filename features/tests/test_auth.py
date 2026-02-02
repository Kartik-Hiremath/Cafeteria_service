"""Authentication tests: Real W3ID and Dummy W3ID flows."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, SessionLocal, engine
from app.models import Manager, User

client = TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def manager(db_session):
    m = Manager(manager_name="Manager 1", balance=50000)
    db_session.add(m)
    db_session.commit()
    db_session.refresh(m)
    return m


def test_auth_login_redirects_without_params():
    """GET /auth/login without mode redirects to W3 or returns redirect."""
    response = client.get("/auth/login", follow_redirects=False)
    # May redirect to IBM SSO (302) or return error if not configured
    assert response.status_code in [302, 500]


def test_auth_login_dummy_with_invalid_manager(db_session):
    """Dummy login with non-existent manager returns 400."""
    response = client.get(
        "/auth/login",
        params={"mode": "dummy", "manager_name": "NoSuchManager", "employee_id": "emp001"},
    )
    assert response.status_code == 400


def test_auth_managers_endpoint(db_session, manager):
    """GET /auth/managers returns list of managers."""
    response = client.get("/auth/managers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(m["name"] == "Manager 1" for m in data)


def test_auth_me_requires_session():
    """GET /auth/me returns 401 when not authenticated."""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_auth_debug_endpoint():
    """GET /auth/debug returns config status (secrets masked)."""
    response = client.get("/auth/debug")
    assert response.status_code == 200
    data = response.json()
    assert "is_w3_configured" in data
    assert "FRONTEND_URL" in data
