from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from bookmark_backup.db import seed_permissions
from bookmark_backup.db.models import Base
from bookmark_backup.db.session import get_db
import bookmark_backup.web.app as web_app
from bookmark_backup.web.app import app


def create_test_client() -> TestClient:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    with TestingSessionLocal() as session:
        seed_permissions(session)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    web_app.SessionLocal = TestingSessionLocal
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_register_and_login_creates_user_and_sets_cookie() -> None:
    client = create_test_client()

    register_payload = {
        "email": "user@example.com",
        "password": "Secret123!",
        "confirm_password": "Secret123!",
        "first_name": "Test",
        "last_name": "User",
    }

    response = client.post("/api/register", json=register_payload)
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"

    user_email_cookie = response.cookies.get("user_email")
    assert user_email_cookie is not None
    assert user_email_cookie.strip('"') == "user@example.com"

    logout_response = client.post("/api/logout")
    assert logout_response.headers.get("set-cookie") is not None
    assert client.cookies.get("user_email") is None

    login_payload = {"email": "user@example.com", "password": "Secret123!"}
    login_response = client.post("/api/login", json=login_payload)
    assert login_response.status_code == 200
    assert login_response.json()["email"] == "user@example.com"
    
    login_user_email_cookie = login_response.cookies.get("user_email")
    assert login_user_email_cookie is not None
    assert login_user_email_cookie.strip('"') == "user@example.com"


def test_logout_clears_cookie_and_protects_current_user_endpoint() -> None:
    client = create_test_client()

    register_payload = {
        "email": "logout-test@example.com",
        "password": "Password1",
        "confirm_password": "Password1",
        "first_name": "Logout",
        "last_name": "Tester",
    }
    client.post("/api/register", json=register_payload)
    logout_response = client.post("/api/logout")

    assert logout_response.headers.get("set-cookie") is not None
    assert client.cookies.get("user_email") is None

    me_response = client.get("/api/me")
    assert me_response.status_code == 401
    assert me_response.json() == {"detail": "Not authenticated"}


def test_get_current_user_requires_authentication() -> None:
    client = create_test_client()

    no_auth_response = client.get("/api/me")
    assert no_auth_response.status_code == 401
    assert no_auth_response.json()["detail"] == "Not authenticated"

    bearer_response = client.get(
        "/api/me",
        headers={"Authorization": "Bearer nonexistent@example.com"},
    )
    assert bearer_response.status_code == 401
    assert bearer_response.json()["detail"] == "User not found"


def test_login_fails_with_invalid_credentials() -> None:
    client = create_test_client()

    invalid_login = client.post(
        "/api/login",
        json={"email": "missing@example.com", "password": "wrong"},
    )
    assert invalid_login.status_code == 401
    assert invalid_login.json()["detail"] == "Invalid credentials"

    register_payload = {
        "email": "bad-password@example.com",
        "password": "CorrectPassword",
        "confirm_password": "CorrectPassword",
        "first_name": "Bad",
        "last_name": "Password",
    }
    client.post("/api/register", json=register_payload)

    wrong_password = client.post(
        "/api/login",
        json={"email": "bad-password@example.com", "password": "incorrect"},
    )
    assert wrong_password.status_code == 401
    assert wrong_password.json()["detail"] == "Invalid credentials"


def test_register_fails_when_passwords_do_not_match() -> None:
    client = create_test_client()

    response = client.post(
        "/api/register",
        json={
            "email": "mismatch@example.com",
            "password": "Password1",
            "confirm_password": "Password2",
            "first_name": "Mismatch",
            "last_name": "Test",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Passwords do not match"

def test_all_protected_endpoints_require_authentication() -> None:
    """Verify all API endpoints (except login/register) require authentication."""
    client = create_test_client()

    # List of protected endpoints with method and required parameters
    protected_endpoints = [
        ("POST", "/api/import"),
        ("GET", "/api/users"),
        ("GET", "/api/me"),
        ("GET", "/api/devices?user_id=1"),
        ("GET", "/api/exports"),
        ("GET", "/api/tree"),
        ("GET", "/api/bookmarks/1"),
        ("PATCH", "/api/bookmarks/1"),
        ("DELETE", "/api/bookmarks/1"),
        ("PATCH", "/api/folders/1"),
        ("DELETE", "/api/folders/1"),
    ]

    for method, path in protected_endpoints:
        response = None
        if method == "GET":
            response = client.get(path)
        elif method == "POST":
            response = client.post(path)
        elif method == "PATCH":
            response = client.patch(path, json={})
        elif method == "DELETE":
            response = client.delete(path)
        else:
            raise ValueError(f"Unsupported method: {method}")

        assert response is not None
        assert response.status_code == 401, f"{method} {path} should return 401, got {response.status_code}"
        assert "Not authenticated" in response.json().get("detail", ""), f"{method} {path} error message incorrect"