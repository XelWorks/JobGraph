import uuid
import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def auth_headers():
    """Helper fixture to create a random user and return their auth headers."""
    with TestClient(app) as client:
        email = f"profile_candidate_{uuid.uuid4().hex[:8]}@example.com"
        password = "SecurePassword123!"
        
        # 1. Register
        register_payload = {
            "email": email,
            "password": password,
            "first_name": "Profile",
            "last_name": "Tester"
        }
        reg_resp = client.post("/api/v1/auth/register", json=register_payload)
        assert reg_resp.status_code == 201
        
        # 2. Login
        login_payload = {
            "email": email,
            "password": password
        }
        login_resp = client.post("/api/v1/auth/login", json=login_payload)
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        
        return {"Authorization": f"Bearer {token}"}

def test_get_profile_not_found(auth_headers):
    """Verify that GET /profile returns 404 if profile is not yet initialized."""
    with TestClient(app) as client:
        response = client.get("/api/v1/profile", headers=auth_headers)
        assert response.status_code == 404
        assert "Profile not found." in response.json()["detail"]

def test_create_and_get_profile_success(auth_headers):
    """Verify creating and retrieving candidate profile works."""
    with TestClient(app) as client:
        payload = {
            "phone": "+1234567890",
            "preferred_roles": ["Backend Engineer", "Tech Lead"],
            "preferred_locations": ["Remote", "New York"],
            "target_salary": 140000,
            "skills": ["Python", "FastAPI", "SQLAlchemy", "MinIO"]
        }
        
        # 1. Create Profile
        create_resp = client.post("/api/v1/profile", json=payload, headers=auth_headers)
        assert create_resp.status_code == 200
        data = create_resp.json()
        assert data["phone"] == "+1234567890"
        assert data["preferred_roles"] == ["Backend Engineer", "Tech Lead"]
        assert data["preferred_locations"] == ["Remote", "New York"]
        assert data["target_salary"] == 140000
        assert data["skills"] == ["Python", "FastAPI", "SQLAlchemy", "MinIO"]
        assert data["master_resume_url"] is None
        
        # 2. Get Profile
        get_resp = client.get("/api/v1/profile", headers=auth_headers)
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["phone"] == "+1234567890"
        assert get_data["skills"] == ["Python", "FastAPI", "SQLAlchemy", "MinIO"]

def test_profile_validation_failures(auth_headers):
    """Verify validation checks on target salary and empty skills list."""
    with TestClient(app) as client:
        # 1. Negative salary check
        payload_neg_salary = {
            "phone": "+123",
            "preferred_roles": ["Engineer"],
            "target_salary": -500,
            "skills": ["Python"]
        }
        resp = client.post("/api/v1/profile", json=payload_neg_salary, headers=auth_headers)
        assert resp.status_code == 422  # Pydantic validation error

        # 2. Empty skills check
        payload_empty_skills = {
            "phone": "+123",
            "preferred_roles": ["Engineer"],
            "target_salary": 100000,
            "skills": []
        }
        resp2 = client.post("/api/v1/profile", json=payload_empty_skills, headers=auth_headers)
        assert resp2.status_code == 422  # Pydantic field validation error

        # 3. Empty/blank strings skills check
        payload_blank_skills = {
            "phone": "+123",
            "preferred_roles": ["Engineer"],
            "target_salary": 100000,
            "skills": ["   ", "  "]
        }
        resp3 = client.post("/api/v1/profile", json=payload_blank_skills, headers=auth_headers)
        assert resp3.status_code == 422
        assert "skills list cannot be empty" in str(resp3.json()["detail"]).lower()

def test_upload_resume_success(auth_headers):
    """Verify PDF/Docx uploading and pre-signed URL retrieval from MinIO."""
    with TestClient(app) as client:
        # Create a dummy PDF content
        dummy_file = io.BytesIO(b"%PDF-1.4 mock pdf content")
        files = {"file": ("my_resume.pdf", dummy_file, "application/pdf")}
        
        response = client.post("/api/v1/profile/resume", files=files, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["master_resume_url"] is not None
        assert "http" in data["master_resume_url"]
        assert "my_resume.pdf" in data["master_resume_url"]

def test_upload_resume_invalid_type(auth_headers):
    """Verify that uploading non-pdf/docx files returns a 400 error."""
    with TestClient(app) as client:
        dummy_file = io.BytesIO(b"executable content")
        files = {"file": ("virus.exe", dummy_file, "application/x-msdownload")}
        
        response = client.post("/api/v1/profile/resume", files=files, headers=auth_headers)
        assert response.status_code == 400
        assert "pdf or word" in response.json()["detail"].lower()
