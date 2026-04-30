import uuid
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.auth import router as auth_router
from src.api.users import router as users_router
from src.schemas.token import TokenPayloadSchema
from src.schemas.user import UserCreateSchema, UserResponseSchema, UserUpdateSchema
from src.service import AuthService
from src.token.token import Token
from src.utils.roles import RoleEnum


class FakeAuthService:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    @staticmethod
    def _user(role: RoleEnum = RoleEnum.WORKER) -> UserResponseSchema:
        return UserResponseSchema(
            id=uuid.uuid4(),
            email="user@example.com",
            role=role,
            created_by=uuid.uuid4(),
        )

    async def create_user(self, schema: UserCreateSchema, creator_id: uuid.UUID | None = None):
        self.calls.append(("create_user", schema.email, schema.role.value, creator_id))
        role = RoleEnum.ORGANIZATION if schema.role == RoleEnum.ORGANIZATION else RoleEnum.WORKER
        return self._user(role=role)

    async def login(self, email: str, password_text: str):
        self.calls.append(("login", email, password_text))
        return {"access_token": "token", "token_type": "bearer"}

    async def read_user(self, id: uuid.UUID | None = None, email: str | None = None):
        self.calls.append(("read_user", id, email))
        return self._user(role=RoleEnum.WORKER)

    async def update_user(self, user_id: uuid.UUID, schema: UserUpdateSchema) -> None:
        self.calls.append(("update_user", user_id, schema.email))

    async def delete_user(self, user_id: uuid.UUID) -> None:
        self.calls.append(("delete_user", user_id))

    async def read_created_users(self, organization_id: uuid.UUID):
        self.calls.append(("read_created_users", organization_id))
        return [self._user(role=RoleEnum.WORKER)]

    async def delete_worker(self, organization_id: uuid.UUID, worker_id: uuid.UUID) -> None:
        self.calls.append(("delete_worker", organization_id, worker_id))


def _payload(role: str, sub: str | None = None) -> TokenPayloadSchema:
    return TokenPayloadSchema(
        iat=datetime.utcnow(),
        exp=datetime.utcnow() + timedelta(minutes=30),
        sub=sub or str(uuid.uuid4()),
        role=role,
        email="user@example.com",
        org=str(uuid.uuid4()),
    )


def _client_with_overrides(fake_service: FakeAuthService) -> TestClient:
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(users_router)
    app.dependency_overrides[AuthService] = lambda: fake_service
    app.dependency_overrides[Token.verify_token] = lambda: _payload("worker")
    app.dependency_overrides[Token.verify_organization] = lambda: _payload("organization")
    return TestClient(app)


def test_auth_endpoints_positive_paths() -> None:
    fake_service = FakeAuthService()
    client = _client_with_overrides(fake_service)

    register = client.post(
        "/api/auth/register",
        json={"email": "new@example.com", "text_password": "StrongPass123!", "role": "worker"},
    )
    assert register.status_code == 201

    token = client.post(
        "/api/auth/token",
        data={"username": "new@example.com", "password": "StrongPass123!"},
    )
    assert token.status_code == 200
    assert token.json()["token_type"] == "bearer"

    introspect = client.post("/api/auth/introspect")
    assert introspect.status_code == 200

    create_user = client.post(
        "/api/auth/users",
        json={"email": "worker@example.com", "text_password": "StrongPass123!", "role": "worker"},
    )
    assert create_user.status_code == 201

    me = client.get("/api/auth/users/me")
    assert me.status_code == 200

    update_me = client.put(
        "/api/auth/users/me",
        json={"email": "updated@example.com", "text_password": "StrongPass123!"},
    )
    assert update_me.status_code == 204

    workers = client.get("/api/auth/users/workers")
    assert workers.status_code == 200
    assert len(workers.json()) == 1

    worker_id = str(uuid.uuid4())
    delete_worker = client.delete(f"/api/auth/users/workers/{worker_id}")
    assert delete_worker.status_code == 204

    delete_me = client.delete("/api/auth/users/me")
    assert delete_me.status_code == 204

    called_methods = [call[0] for call in fake_service.calls]
    assert "create_user" in called_methods
    assert "login" in called_methods
    assert "read_user" in called_methods
    assert "update_user" in called_methods
    assert "read_created_users" in called_methods
    assert "delete_worker" in called_methods
    assert "delete_user" in called_methods


def test_auth_endpoint_negative_validation() -> None:
    fake_service = FakeAuthService()
    client = _client_with_overrides(fake_service)

    response = client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "text_password": "123", "role": "worker"},
    )
    assert response.status_code == 422


def test_auth_delete_worker_requires_uuid() -> None:
    fake_service = FakeAuthService()
    client = _client_with_overrides(fake_service)

    response = client.delete("/api/auth/users/workers/not-a-uuid")
    assert response.status_code == 422


def test_auth_token_requires_form_data_fields() -> None:
    fake_service = FakeAuthService()
    client = _client_with_overrides(fake_service)

    response = client.post("/api/auth/token", data={"username": "user@example.com"})
    assert response.status_code == 422
