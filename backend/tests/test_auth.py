"""Authentication endpoint tests — register, login, token validation."""


def test_register_user(client):
    """POST /auth/register should create a new user."""
    resp = client.post("/api/v1/auth/register", json={
        "email": "newuser@test.com",
        "username": "newuser",
        "password": "SecurePass123!",
    })
    # May return 200 or 409 if already registered
    assert resp.status_code in (200, 409)


def test_login_with_valid_credentials(client):
    """POST /auth/login with valid credentials should return token."""
    # Register first
    client.post("/api/v1/auth/register", json={
        "email": "loginuser@test.com",
        "username": "loginuser",
        "password": "SecurePass123!",
    })

    resp = client.post("/api/v1/auth/login", json={
        "email": "loginuser@test.com",
        "password": "SecurePass123!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_invalid_password(client):
    """POST /auth/login with wrong password should return 401."""
    client.post("/api/v1/auth/register", json={
        "email": "wrongpass@test.com",
        "username": "wrongpass",
        "password": "SecurePass123!",
    })

    resp = client.post("/api/v1/auth/login", json={
        "email": "wrongpass@test.com",
        "password": "WrongPassword!",
    })
    assert resp.status_code == 401


def test_auth_me_endpoint(client):
    """GET /auth/me should return user data with valid token."""
    # Register + login
    client.post("/api/v1/auth/register", json={
        "email": "meuser@test.com",
        "username": "meuser",
        "password": "SecurePass123!",
    })
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "meuser@test.com",
        "password": "SecurePass123!",
    })
    token = login_resp.json().get("access_token", "")

    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "meuser@test.com"


def test_auth_me_without_token(client):
    """GET /auth/me without token should return 401."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
