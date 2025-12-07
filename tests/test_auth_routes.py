import uuid

import pytest
from sqlalchemy import select

from src.models.profile import Profile
from src.models.users import User


@pytest.mark.anyio
async def test_register_creates_user_and_profile(client, db_session):
    payload = {
        "username": f"user_{uuid.uuid4().hex[:6]}",
        "email": f"{uuid.uuid4().hex[:6]}@example.com",
        "password": "supersecret",
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == payload["email"]
    assert data["access_token"]
    assert data["refresh_token"]

    user_result = await db_session.execute(select(User).where(User.email == payload["email"]))
    user = user_result.scalar_one()
    profile_result = await db_session.execute(select(Profile).where(Profile.user_id == user.id))
    assert profile_result.scalar_one() is not None


@pytest.mark.anyio
async def test_login_returns_tokens_for_existing_user(client, user_factory):
    password = "strong_password"
    user = await user_factory(password=password)

    response = await client.post(
        "/auth/login",
        json={"email": user.email, "password": password},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == user.id
    assert data["access_token"]
    assert data["refresh_token"]


@pytest.mark.anyio
async def test_get_current_user_endpoint_returns_profile(client, user_factory, auth_override):
    user = await user_factory()
    auth_override(user)

    response = await client.get("/auth/current_user")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["email"] == user.email


@pytest.mark.anyio
async def test_logout_clears_refresh_token_even_without_cookie(client, user_factory, auth_override):
    user = await user_factory()
    auth_override(user)

    response = await client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully logged out"
