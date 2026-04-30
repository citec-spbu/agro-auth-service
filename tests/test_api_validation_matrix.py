import uuid
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.auth import router as auth_router
from src.api.users import router as users_router
from src.schemas.token import TokenPayloadSchema
from src.service import AuthService
from src.token.token import Token
from tests.test_api_business import FakeAuthService


def _payload(role: str) -> TokenPayloadSchema:
    return TokenPayloadSchema(
        iat=datetime.utcnow(),
        exp=datetime.utcnow() + timedelta(minutes=30),
        sub=str(uuid.uuid4()),
        role=role,
        email="user@example.com",
        org=str(uuid.uuid4()),
    )


def _client() -> TestClient:
    fake = FakeAuthService()
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(users_router)
    app.dependency_overrides[AuthService] = lambda: fake
    app.dependency_overrides[Token.verify_token] = lambda: _payload("worker")
    app.dependency_overrides[Token.verify_organization] = lambda: _payload("organization")
    return TestClient(app)


@pytest.mark.parametrize(
    ("method", "path", "json_body", "data_body", "expected_status"),
    [
        ("post", "/api/auth/register", {"email": "ok@example.com", "text_password": "StrongPass123!", "role": "worker"}, None, 201),
        ("post", "/api/auth/register", {"email": "bad", "text_password": "StrongPass123!", "role": "worker"}, None, 422),
        ("post", "/api/auth/register", {"email": "ok@example.com", "text_password": "123", "role": "worker"}, None, 422),
        ("post", "/api/auth/register", {"email": "ok@example.com", "text_password": "StrongPass123!", "role": "bad"}, None, 422),
        ("post", "/api/auth/token", None, {"username": "u", "password": "p"}, 200),
        ("post", "/api/auth/token", None, {"username": "u"}, 422),
        ("post", "/api/auth/token", None, {"password": "p"}, 422),
        ("post", "/api/auth/introspect", None, None, 200),
        ("get", "/api/auth/users/me", None, None, 200),
        ("put", "/api/auth/users/me", {"email": "u@example.com", "text_password": "StrongPass123!"}, None, 204),
        ("put", "/api/auth/users/me", {"email": "bad", "text_password": "StrongPass123!"}, None, 422),
        ("put", "/api/auth/users/me", {"email": "u@example.com", "text_password": "123"}, None, 422),
        ("delete", "/api/auth/users/me", None, None, 204),
        ("get", "/api/auth/users/workers", None, None, 200),
        ("post", "/api/auth/users", {"email": "w@example.com", "text_password": "StrongPass123!", "role": "worker"}, None, 201),
        ("post", "/api/auth/users", {"email": "bad", "text_password": "StrongPass123!", "role": "worker"}, None, 422),
        ("delete", f"/api/auth/users/workers/{uuid.uuid4()}", None, None, 204),
        ("delete", "/api/auth/users/workers/not-a-uuid", None, None, 422),
        ("post", "/api/auth/register", {"email": "ok@example.com"}, None, 422),
        ("post", "/api/auth/users", {"role": "worker"}, None, 422),
    ],
)
def test_auth_validation_matrix(
    method: str,
    path: str,
    json_body: dict | None,
    data_body: dict | None,
    expected_status: int,
) -> None:
    client = _client()
    response = client.request(method.upper(), path, json=json_body, data=data_body)
    assert response.status_code == expected_status
