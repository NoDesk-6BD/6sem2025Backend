import pytest


@pytest.mark.asyncio
async def test_create_user_ok(client):
    payload = {
        "email": " Alice@Example.COM ",
        "password": "ChangeMe123!",
        "full_name": "Alice",
        "phone": "11 99999-0000",
        "cpf": "123.456.789-01",
        "vip": True,
    }
    r = await client.post("/users/", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["id"] > 0
    assert data["email"] == "alice@example.com"  # normalized lower
    assert data["cpf"] == "12345678901"  # digits only
    assert data["vip"] is True
    assert data["active"] is True
    # password must not be present in response
    assert "encrypted_password" not in data


@pytest.mark.asyncio
async def test_list_and_get_user(client):
    # list should contain at least one (Alice)
    r = await client.get("/users/")
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    assert any(u["email"] == "alice@example.com" for u in items)

    # get by id
    uid = items[0]["id"]
    r = await client.get(f"/users/{uid}")
    assert r.status_code == 200
    got = r.json()
    assert got["id"] == uid


# @pytest.mark.asyncio
# async def test_unique_conflicts_email_and_cpf(client):
#     # First user
#     r = await client.post(
#         "/users/",
#         json={
#             "email": "bob@example.com",
#             "password": "Secret123!",
#             "cpf": "98765432100",
#         },
#     )
#     assert r.status_code == 201

#     # Duplicate email
#     r = await client.post(
#         "/users/",
#         json={
#             "email": "bob@example.com",
#             "password": "OtherPass!2",
#             "cpf": "11122233344",
#         },
#     )
#     assert r.status_code == 409

#     # Duplicate CPF
#     r = await client.post(
#         "/users/",
#         json={
#             "email": "bob2@example.com",
#             "password": "OtherPass!2",
#             "cpf": "987.654.321-00",
#         },
#     )
#     assert r.status_code == 409


@pytest.mark.asyncio
async def test_update_user_normalizes_and_checks_uniques(client):
    # Create Bob first
    r = await client.post(
        "/users/",
        json={
            "email": "bob@example.com",
            "password": "Secret123!",
            "cpf": "98765432100",
            "full_name": "Bob",
        },
    )
    assert r.status_code == 201

    # Create Charlie
    r = await client.post(
        "/users/",
        json={
            "email": "charlie@example.com",
            "password": "Secret123!",
            "cpf": "11122233300",
            "full_name": "Charlie",
        },
    )
    assert r.status_code == 201
    uid = r.json()["id"]

    # Try to change email to existing bob@example.com
    r = await client.put(
        f"/users/{uid}",
        json={"email": "BOB@EXAMPLE.COM"},
    )
    assert r.status_code == 409

    # Valid update (normalize cpf and email)
    r = await client.put(
        f"/users/{uid}",
        json={"email": " charlie2@Example.com ", "cpf": "111.222.333-00"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "charlie2@example.com"
    assert data["cpf"] == "11122233300"


@pytest.mark.asyncio
async def test_delete_user_and_404(client):
    # Create a disposable user
    r = await client.post(
        "/users/",
        json={
            "email": "delete.me@example.com",
            "password": "Tmp123!!",
            "cpf": "00011122233",
        },
    )
    assert r.status_code == 201
    uid = r.json()["id"]

    # Delete
    r = await client.delete(f"/users/{uid}")
    assert r.status_code == 204

    # Fetch -> 404
    r = await client.get(f"/users/{uid}")
    assert r.status_code == 404
