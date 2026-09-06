import uuid

import pytest
from app.domain.auth import User
from app.domain.vault import SessionVault
from app.infrastructure.db.session import SessionLocal
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import delete, select


@pytest.mark.asyncio
async def test_vault_full_lifecycle():
    """
    Integration Test: Session Vault Full Lifecycle
    1. Register a test user and obtain JWT token.
    2. POST portal session payload to /api/v1/vault.
    3. Read encrypted DB column directly to verify AES-256-GCM cipher text.
    4. Call GET /api/v1/vault/{portal}/decrypt to verify decrypted payload.
    5. Update portal health status and verify changes.
    6. Delete portal entry and verify DB cleanup in teardown.
    """
    test_id = uuid.uuid4().hex[:8]
    email = f"vault_test_{test_id}@example.com"
    password = "VaultTestPassword123!"
    portal_name = "LinkedIn"
    session_payload = '{"cookies": "session=abc123; csrf=xyz789"}'

    with TestClient(app) as client:
        # Step 1: Register user
        reg_resp = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "first_name": "Vault",
            "last_name": "Tester"
        })
        assert reg_resp.status_code == 201
        user_id = uuid.UUID(reg_resp.json()["id"])

        # Step 2: Login to obtain JWT
        login_resp = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 3: POST portal session payload to vault
        vault_resp = client.post("/api/v1/vault", json={
            "portal_name": portal_name,
            "session_payload": session_payload,
            "status": "Healthy"
        }, headers=headers)
        assert vault_resp.status_code == 201
        vault_data = vault_resp.json()
        assert vault_data["portal_name"] == portal_name
        assert vault_data["status"] == "Healthy"
        vault_entry_id = uuid.UUID(vault_data["id"])

        # Step 4: Read encrypted DB column directly to verify AES-256-GCM cipher text
        async with SessionLocal() as session:
            result = await session.execute(
                select(SessionVault).where(SessionVault.id == vault_entry_id)
            )
            db_entry = result.scalar_one_or_none()
            assert db_entry is not None
            assert db_entry.encrypted_session_payload != session_payload
            assert db_entry.encrypted_session_payload != ""
            # Verify it's not plaintext — cipher text should not contain original payload
            assert session_payload not in db_entry.encrypted_session_payload
            # Verify it's valid hex (nonce + ciphertext)
            int(db_entry.encrypted_session_payload, 16)

        # Step 5: Call GET /api/v1/vault/{portal}/decrypt to verify decrypted payload
        decrypt_resp = client.get(
            f"/api/v1/vault/{portal_name}/decrypt",
            headers=headers
        )
        assert decrypt_resp.status_code == 200
        decrypt_data = decrypt_resp.json()
        assert decrypt_data["portal_name"] == portal_name
        assert decrypt_data["session_payload"] == session_payload

        # Step 6: Update portal health status
        update_resp = client.post("/api/v1/vault", json={
            "portal_name": portal_name,
            "session_payload": session_payload,
            "status": "Reconnect Required"
        }, headers=headers)
        assert update_resp.status_code == 201
        assert update_resp.json()["status"] == "Reconnect Required"

        # Step 7: Verify GET /api/v1/vault lists the updated status
        list_resp = client.get("/api/v1/vault", headers=headers)
        assert list_resp.status_code == 200
        vaults = list_resp.json()
        assert len(vaults) >= 1
        linkedin_vault = next(
            (v for v in vaults if v["portal_name"] == portal_name),
            None
        )
        assert linkedin_vault is not None
        assert linkedin_vault["status"] == "Reconnect Required"

        # Step 8: Verify unauthorized request is rejected with 401
        unauth_resp = client.get("/api/v1/vault")
        assert unauth_resp.status_code == 401

        unauth_decrypt_resp = client.get(f"/api/v1/vault/{portal_name}/decrypt")
        assert unauth_decrypt_resp.status_code == 401

        # Step 9: Delete portal entry
        delete_resp = client.delete(f"/api/v1/vault/{portal_name}", headers=headers)
        assert delete_resp.status_code == 204

        # Step 10: Verify entry is removed from DB
        async with SessionLocal() as session:
            result = await session.execute(
                select(SessionVault).where(SessionVault.id == vault_entry_id)
            )
            deleted_entry = result.scalar_one_or_none()
            assert deleted_entry is None

        # Step 11: Verify 404 when trying to decrypt deleted entry
        decrypt_after_delete = client.get(
            f"/api/v1/vault/{portal_name}/decrypt",
            headers=headers
        )
        assert decrypt_after_delete.status_code == 404

        # Step 12: Verify 404 when trying to delete non-existent entry
        delete_nonexistent = client.delete(
            "/api/v1/vault/NonExistentPortal",
            headers=headers
        )
        assert delete_nonexistent.status_code == 404

        # Teardown: Delete user from DB
        async with SessionLocal() as session:
            await session.execute(delete(User).where(User.id == user_id))
            await session.commit()

            # Verify user is deleted
            deleted_user = await session.get(User, user_id)
            assert deleted_user is None

@pytest.mark.asyncio
async def test_browser_profile_routes_and_reconnect_contract():
    test_id = uuid.uuid4().hex[:8]
    email = f"profile_routes_{test_id}@example.com"
    password = "ProfileRoutePassword123!"

    with TestClient(app) as client:
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "first_name": "Profile",
                "last_name": "Tester",
            },
        )
        assert reg_resp.status_code == 201

        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        save_resp = client.post(
            "/api/v1/vault",
            json={
                "portal_name": "LinkedIn",
                "session_payload": '{"cookies": ["linkedin-session"]}',
                "status": "Healthy",
            },
            headers=headers,
        )
        assert save_resp.status_code == 201

        profiles_resp = client.get("/api/v1/vault/profiles", headers=headers)
        assert profiles_resp.status_code == 200
        profile_list = profiles_resp.json()
        assert any(p["profile_name"] == "LinkedIn" for p in profile_list)

        reconnect_resp = client.post(
            "/api/v1/vault/LinkedIn/reconnect",
            headers=headers,
        )
        assert reconnect_resp.status_code == 200
        assert reconnect_resp.json()["portal_name"] == "LinkedIn"

        delete_resp = client.delete("/api/v1/vault/profiles/LinkedIn", headers=headers)
        assert delete_resp.status_code == 204

        async with SessionLocal() as session:
            await session.execute(delete(User).where(User.email == email))
            await session.commit()