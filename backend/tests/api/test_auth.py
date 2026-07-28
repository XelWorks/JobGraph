import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.auth import hash_password, verify_password, decode_access_token

def test_argon2_password_hashing():
    """Verify password hashing and verification conforms to Argon2id."""
    password = "SuperSecretPassword123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert hashed.startswith("$argon2id$")
    
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_auth_integration_flow():
    """Verify full authentication flow: registration, login, token validation, and error scenarios."""
    import uuid
    email = f"candidate_{uuid.uuid4().hex[:8]}@example.com"
    
    with TestClient(app) as client:
        # 1. Register a new user
        register_payload = {
            "email": email,
            "password": "SecurePassword123!",
            "first_name": "John",
            "last_name": "Doe"
        }
        response = client.post("/api/v1/auth/register", json=register_payload)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["email"] == email
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["is_active"] is True
        
        # 2. Duplicate registration check
        dup_response = client.post("/api/v1/auth/register", json=register_payload)
        assert dup_response.status_code == 400
        assert "exists" in dup_response.json()["detail"]
        
        # 3. Invalid email registration check
        invalid_email_payload = register_payload.copy()
        invalid_email_payload["email"] = "invalid-email-format"
        invalid_response = client.post("/api/v1/auth/register", json=invalid_email_payload)
        assert invalid_response.status_code == 400
        assert "email" in invalid_response.json()["detail"].lower()

        # 4. Successful login
        login_payload = {
            "email": email,
            "password": "SecurePassword123!"
        }
        login_response = client.post("/api/v1/auth/login", json=login_payload)
        assert login_response.status_code == 200
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        
        # 5. Token validation check
        payload = decode_access_token(token_data["access_token"])
        assert payload is not None
        assert payload["sub"] == email
        
        # 6. Failed login check (Incorrect password)
        wrong_pass_payload = {
            "email": email,
            "password": "WrongPassword!"
        }
        failed_response1 = client.post("/api/v1/auth/login", json=wrong_pass_payload)
        assert failed_response1.status_code == 401
        assert failed_response1.json()["detail"] == "Invalid credentials"
        
        # 7. Failed login check (Non-existent email)
        wrong_email_payload = {
            "email": f"nonexistent_{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePassword123!"
        }
        failed_response2 = client.post("/api/v1/auth/login", json=wrong_email_payload)
        assert failed_response2.status_code == 401
        assert failed_response2.json()["detail"] == "Invalid credentials"
