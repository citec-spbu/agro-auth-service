from src.main import app
from src.token.token import Token


def test_auth_routes_are_registered() -> None:
    paths = {route.path for route in app.routes}

    assert "/api/auth/register" in paths
    assert "/api/auth/token" in paths
    assert "/api/auth/introspect" in paths
    assert "/api/auth/users/me" in paths


def test_password_hash_round_trip() -> None:
    password = "StrongPass123!"
    password_hash = Token.get_password_hash(password)

    assert password_hash != password
    assert Token.verify_password(password, password_hash)
