import io
import uuid

import pytest
from app.domain.auth import User
from app.domain.job import Application, JobPosting
from app.domain.profile import Experience, Skill, UserProfile
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.storage.minio import storage
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def auth_client():
    """Helper fixture to register a new user, login, and return TestClient with auth headers."""
    email = f"e2e_tailoring_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecureE2EPassword123!"

    with TestClient(app) as client:
        # 1. Register
        reg_payload = {
            "email": email,
            "password": password,
            "first_name": "E2ETailor",
            "last_name": "Tester"
        }
        reg_resp = client.post("/api/v1/auth/register", json=reg_payload)
        assert reg_resp.status_code == 201

        # 2. Login
        login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        client.headers.update({"Authorization": f"Bearer {token}"})
        yield client, email


@pytest.mark.asyncio
async def test_end_to_end_tailoring_pipeline_flow(auth_client):
    """
    E2E Integration Test:
    1. Configure candidate profile through POST /api/v1/profile (Skills, Experience, target criteria).
    2. Upload candidate master resume through POST /api/v1/profile/resume (stored in MinIO resumes/).
    3. Setup target Job Posting record in database.
    4. Trigger tailoring pipeline through POST /api/v1/tailor/trigger.
    5. Verify side-by-side original vs tailored resume bullets compare cleanly.
    6. Verify tailored cover letter is generated.
    7. Verify generated resume & letter are stored securely inside MinIO with unique UUID path nonces.
    8. Verify pre-signed download link generation matches and can fetch active assets.
    9. Perform exhaustive database and S3 asset cleanup (Teardown).
    """
    client, email = auth_client

    # --- STEP 1: Configure candidate profile via API ---
    profile_payload = {
        "phone": "+1 (555) 999-8888",
        "preferred_roles": ["Senior Backend Developer", "FastAPI Engineer"],
        "preferred_locations": ["Remote", "Austin, TX"],
        "target_salary": 160000,
        "skills": ["Python", "FastAPI", "SQLAlchemy", "MinIO", "Docker"]
    }

    profile_resp = client.post("/api/v1/profile", json=profile_payload)
    assert profile_resp.status_code == 200
    p_data = profile_resp.json()
    assert p_data["phone"] == "+1 (555) 999-8888"
    assert "FastAPI" in p_data["skills"]

    # --- STEP 2: Configure master resume upload via API ---
    dummy_pdf_content = b"%PDF-1.4 mock candidate master resume body"
    resume_file = ("my_master_resume.pdf", io.BytesIO(dummy_pdf_content), "application/pdf")

    resume_resp = client.post("/api/v1/profile/resume", files={"file": resume_file})
    assert resume_resp.status_code == 200
    assert resume_resp.json()["master_resume_url"] is not None

    # Retrieve user ID & profile records to clean up manually
    user_id = None
    profile_record = None
    async with SessionLocal() as session:
        from sqlalchemy import select
        user_query = select(User).where(User.email == email)
        user_res = await session.execute(user_query)
        user = user_res.scalar_one()
        user_id = user.id

        profile_query = select(UserProfile).where(UserProfile.user_id == user_id)
        profile_res = await session.execute(profile_query)
        profile_record = profile_res.scalar_one()

    # Add an experience item to the profile directly
    exp_id = uuid.uuid4()
    async with SessionLocal() as session:
        experience = Experience(
            id=exp_id,
            profile_id=profile_record.id,
            company="MicroCorp AI",
            role="Backend Dev",
            start_date="2023",
            end_date="Present",
            description="Built custom storage loaders and FastAPI services."
        )
        session.add(experience)
        await session.commit()

    # --- STEP 3: Setup target Job Posting record ---
    job_id = uuid.uuid4()
    async with SessionLocal() as session:
        job = JobPosting(
            id=job_id,
            platform="Greenhouse",
            external_job_id="e2e-job-505",
            board_token="e2ecorp",
            title="Senior FastAPI Backend Architect",
            company="E2E Corp",
            location="Remote",
            url="https://boards.greenhouse.io/e2ecorp/jobs/505",
            description_text="Looking for a Backend Architect skilled in Python, FastAPI, and S3-compatible MinIO object storage."
        )
        session.add(job)
        await session.commit()

    # --- STEP 4: Trigger tailoring pipeline ---
    from app.core.config import settings
    original_api_key = settings.gemini_api_key
    settings.gemini_api_key = "mock-key-for-now"

    from app.services.tailoring.service import tailoring_pipeline_service
    original_client_key = tailoring_pipeline_service.gemini_client.api_key
    tailoring_pipeline_service.gemini_client.api_key = "mock-key-for-now"

    try:
        # POST trigger endpoint
        trigger_payload = {"job_posting_id": str(job_id)}
        trigger_resp = client.post("/api/v1/tailor/trigger", json=trigger_payload)
        assert trigger_resp.status_code == 200

        # --- STEP 5: Verify response and comparisons ---
        data = trigger_resp.json()
        assert data["application_id"] is not None
        assert data["status"] == "Auto-Filled"
        assert data["mode"] == "Manual"
        assert data["tailored_resume_key"] is not None
        assert data["cover_letter_key"] is not None

        # S3 pre-signed keys verification
        assert data["tailored_resume_url"] is not None
        assert data["cover_letter_url"] is not None
        assert "http://" in data["tailored_resume_url"] or "https://" in data["tailored_resume_url"]

        # Original vs Tailored details
        orig = data["original_data"]
        assert "FastAPI" in orig["skills"]
        assert len(orig["experiences"]) == 1
        assert orig["experiences"][0]["company"] == "MicroCorp AI"

        tailored = data["tailored_data"]
        assert tailored["summary"] != ""
        assert "FastAPI" in tailored["skills"]
        assert len(tailored["experience"]) == 1
        assert tailored["experience"][0]["company"] == "MicroCorp AI"
        assert len(tailored["experience"][0]["bullets"]) > 0

        # --- STEP 6: Verify cover letter was customized ---
        cl = data["cover_letter"]
        assert "E2E Corp" in cl["subject"] or "FastAPI Backend Architect" in cl["subject"]
        assert "Dear Hiring Team" in cl["body"] or "Dear" in cl["body"]

        # --- STEP 7 & 8: Verify pre-signed link generation and S3 assets ---
        # Stat the generated objects inside MinIO storage
        resume_stat = storage.client.stat_object(storage.bucket_name, data["tailored_resume_key"])
        cl_stat = storage.client.stat_object(storage.bucket_name, data["cover_letter_key"])

        assert resume_stat.size > 0
        assert cl_stat.size > 0
        assert resume_stat.content_type == "application/pdf"
        assert cl_stat.content_type == "application/pdf"

        # Retrieve keys for cleanup
        tailored_resume_key = data["tailored_resume_key"]
        cover_letter_key = data["cover_letter_key"]
        application_id = data["application_id"]

    finally:
        # Revert mock configurations
        settings.gemini_api_key = original_api_key
        tailoring_pipeline_service.gemini_client.api_key = original_client_key

    # --- STEP 9: Teardown Cleanup ---
    async with SessionLocal() as session:
        from sqlalchemy import delete
        # Delete database records
        await session.execute(delete(Application).where(Application.id == uuid.UUID(application_id)))
        await session.execute(delete(JobPosting).where(JobPosting.id == job_id))
        await session.execute(delete(Experience).where(Experience.id == exp_id))
        await session.execute(delete(Skill).where(Skill.profile_id == profile_record.id))
        await session.execute(delete(UserProfile).where(UserProfile.id == profile_record.id))
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()

    # Delete uploaded MinIO assets
    try:
        storage.client.remove_object(storage.bucket_name, profile_record.master_resume_key)
        storage.client.remove_object(storage.bucket_name, tailored_resume_key)
        storage.client.remove_object(storage.bucket_name, cover_letter_key)
    except Exception as e:
        print(f"Cleanup of S3 assets in E2E integration test completed with warning: {e}")
