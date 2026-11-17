import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_cross_tenant_access_denial(client: AsyncClient):
    """Verifies that an authenticated member of Org A cannot access or tamper with Org B."""
    # Register User A and create Org A
    user_a_email = f"usera_{uuid.uuid4().hex[:8]}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": user_a_email, "password": "Password123!", "full_name": "User Alpha"},
    )
    res_a = await client.post(
        "/api/v1/auth/login",
        json={"email": user_a_email, "password": "Password123!"},
    )
    token_a = res_a.json()["data"]["access_token"]

    org_a_res = await client.post(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"name": f"Org Alpha {uuid.uuid4().hex[:6]}"},
    )
    org_a_id = org_a_res.json()["data"]["id"]

    # Register User B and create Org B
    user_b_email = f"userb_{uuid.uuid4().hex[:8]}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": user_b_email, "password": "Password123!", "full_name": "User Beta"},
    )
    res_b = await client.post(
        "/api/v1/auth/login",
        json={"email": user_b_email, "password": "Password123!"},
    )
    token_b = res_b.json()["data"]["access_token"]

    org_b_res = await client.post(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"name": f"Org Beta {uuid.uuid4().hex[:6]}"},
    )
    org_b_id = org_b_res.json()["data"]["id"]

    # User A tries to inspect Org B by passing Org B ID in header
    malicious_headers = {
        "Authorization": f"Bearer {token_a}",
        "X-Organization-ID": org_b_id,
    }
    tamper_res = await client.get(
        f"/api/v1/organizations/{org_b_id}",
        headers=malicious_headers,
    )
    # RLS/dependency denies membership: 403 Forbidden
    assert tamper_res.status_code == 403
    assert tamper_res.json()["error"]["code"] == "FORBIDDEN"

    # User A tries to update Org B
    tamper_patch = await client.patch(
        f"/api/v1/organizations/{org_b_id}",
        headers=malicious_headers,
        json={"name": "Hacked Org Name"},
    )
    assert tamper_patch.status_code == 403
    assert tamper_patch.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.anyio
async def test_sole_admin_removal_forbidden(client: AsyncClient):
    """Verifies that an organization's sole administrator cannot be deleted."""
    email = f"soleadmin_{uuid.uuid4().hex[:8]}@example.com"
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Sole Admin"},
    )
    user_id = reg.json()["data"]["id"]
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = login.json()["data"]["access_token"]

    org_res = await client.post(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": f"Single Admin Org {uuid.uuid4().hex[:6]}"},
    )
    org_id = org_res.json()["data"]["id"]

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": org_id,
    }

    # Attempt to remove the sole admin
    del_res = await client.delete(
        f"/api/v1/organizations/{org_id}/members/{user_id}",
        headers=headers,
    )
    assert del_res.status_code == 409
    assert del_res.json()["error"]["code"] == "CONFLICT"
    assert "sole administrator" in del_res.json()["error"]["message"]
