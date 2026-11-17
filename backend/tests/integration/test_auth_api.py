import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_auth_registration_and_duplicate_handling(client: AsyncClient):
    unique_email = f"alice_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": unique_email,
        "password": "Password123!",
        "full_name": "Alice Smith",
    }

    # Register user
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["success"] is True
    assert data["data"]["email"] == unique_email
    assert data["data"]["full_name"] == "Alice Smith"
    assert "password" not in data["data"]
    assert "password_hash" not in data["data"]

    # Attempt duplicate registration
    res_dup = await client.post("/api/v1/auth/register", json=payload)
    assert res_dup.status_code == 409
    dup_data = res_dup.json()
    assert dup_data["success"] is False
    assert dup_data["error"]["code"] == "CONFLICT"


@pytest.mark.anyio
async def test_auth_login_and_token_refresh(client: AsyncClient):
    unique_email = f"bob_{uuid.uuid4().hex[:8]}@example.com"
    reg_payload = {
        "email": unique_email,
        "password": "SecretPassword123!",
        "full_name": "Bob Jones",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201

    # Login with wrong password
    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401
    assert bad_login.json()["error"]["code"] == "UNAUTHENTICATED"

    # Login with correct password
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "SecretPassword123!"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()["data"]
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    assert access_token and refresh_token
    assert token_data["token_type"] == "bearer"

    # Call /me endpoint with access token
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == unique_email

    # Refresh tokens
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()["data"]
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"]


@pytest.mark.anyio
async def test_organizations_lifecycle_and_rbac(client: AsyncClient):
    # 1. Register admin user
    admin_email = f"orgadmin_{uuid.uuid4().hex[:8]}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": admin_email, "password": "Password123!", "full_name": "Org Admin"},
    )
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": "Password123!"},
    )
    admin_token = admin_login.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Register regular user
    user_email = f"investigator_{uuid.uuid4().hex[:8]}@example.com"
    user_reg = await client.post(
        "/api/v1/auth/register",
        json={"email": user_email, "password": "Password123!", "full_name": "Investigator Dave"},
    )
    user_id = user_reg.json()["data"]["id"]
    user_login = await client.post(
        "/api/v1/auth/login",
        json={"email": user_email, "password": "Password123!"},
    )
    user_token = user_login.json()["data"]["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 3. Create organization as Admin
    org_name = f"Apex Intel {uuid.uuid4().hex[:6]}"
    org_res = await client.post(
        "/api/v1/organizations/",
        headers=admin_headers,
        json={"name": org_name, "metadata": {"region": "EMEA"}},
    )
    assert org_res.status_code == 201, org_res.text
    org = org_res.json()["data"]
    org_id = org["id"]
    assert org["name"] == org_name

    # Set tenant header for org-scoped calls
    admin_tenant_headers = {
        "Authorization": f"Bearer {admin_token}",
        "X-Organization-ID": org_id,
    }

    # 4. List members (creator is automatically admin)
    members_res = await client.get(
        f"/api/v1/organizations/{org_id}/members",
        headers=admin_tenant_headers,
    )
    assert members_res.status_code == 200
    members = members_res.json()["data"]
    assert len(members) == 1
    assert members[0]["role"] == "ORGANIZATION_ADMIN"

    # 5. Add regular user as investigator
    add_member_res = await client.post(
        f"/api/v1/organizations/{org_id}/members",
        headers=admin_tenant_headers,
        json={"user_id": user_id, "role": "INVESTIGATOR"},
    )
    assert add_member_res.status_code == 201
    assert add_member_res.json()["data"]["role"] == "INVESTIGATOR"

    # 6. Verify regular user can now list organizations
    my_orgs_res = await client.get("/api/v1/organizations/", headers=user_headers)
    assert my_orgs_res.status_code == 200
    org_ids = [o["id"] for o in my_orgs_res.json()["data"]]
    assert org_id in org_ids

    # 7. Non-admin regular user cannot add another member (RBAC enforcement: 403 Forbidden)
    user_tenant_headers = {
        "Authorization": f"Bearer {user_token}",
        "X-Organization-ID": org_id,
    }
    dummy_user_id = str(uuid.uuid4())
    forbidden_add = await client.post(
        f"/api/v1/organizations/{org_id}/members",
        headers=user_tenant_headers,
        json={"user_id": dummy_user_id, "role": "REVIEWER"},
    )
    assert forbidden_add.status_code == 403
    assert forbidden_add.json()["error"]["code"] == "FORBIDDEN"
