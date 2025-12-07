import pytest


@pytest.mark.anyio
async def test_get_profile_returns_data(client, user_factory, auth_override):
    user = await user_factory()
    auth_override(user)

    response = await client.get("/profile/me")
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == user.profile.name
    assert payload["surname"] == user.profile.surname


@pytest.mark.anyio
async def test_create_profile_creates_when_absent(client, user_factory, auth_override, db_session):
    user = await user_factory(with_profile=False)
    auth_override(user)

    profile_payload = {
        "name": "Test",
        "surname": "User",
        "patronymic": "Ivanovich",
        "university": "Test University",
        "faculty": "Engineering",
        "course": 2,
        "group": "B1",
        "city": "Kazan",
        "phone_number": "123",
        "avatar_url": None,
    }
    response = await client.post("/profile/", json=profile_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["group"] == "B1"

    await db_session.refresh(user)
    assert user.profile is not None


@pytest.mark.anyio
async def test_update_profile_overwrites_fields(client, user_factory, auth_override):
    user = await user_factory()
    auth_override(user)

    response = await client.put(
        "/profile/",
        json={
            "name": "Updated",
            "surname": "Profile",
            "patronymic": "Test",
            "university": "Updated University",
            "faculty": "Math",
            "course": 3,
            "group": "C3",
            "city": "Perm",
            "phone_number": "555",
            "avatar_url": None,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Updated"
    assert payload["group"] == "C3"


@pytest.mark.anyio
async def test_delete_profile_removes_profile(client, user_factory, auth_override, db_session):
    user = await user_factory()
    auth_override(user)

    response = await client.delete("/profile/")
    assert response.status_code == 204

    await db_session.refresh(user)
    assert user.profile is None
