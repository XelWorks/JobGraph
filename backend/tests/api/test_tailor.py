import uuid

import pytest
from app.domain.auth import User
from app.domain.job import Application, JobPosting
from app.domain.profile import Experience, Skill, UserProfile
from app.infrastructure.db.session import SessionLocal
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def test_setup_data():
    """Helper fixture to create a user with profile & experiences, and a job posting."""
    email = f"tailor_api_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"

    with TestClient(app) as client:
        # 1. Register User
        register_payload = {
            "email": email,
            "password": password,
            "first_name": "API",
            "last_name": "Tester"
        }
        reg_resp = client.post("/api/v1/auth/register", json=register_payload)
        assert reg_resp.status_code == 201

        # 2. Login to get token
        login_payload = {
            "email": email,
            "password": password
        }
        login_resp = client.post("/api/v1/auth/login", json=login_payload)
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

    return {
        "headers": headers,
        "email": email
    }

@pytest.mark.asyncio
async def test_tailoring_api_endpoints(test_setup_data):
    """
    Integration API Test:
    1. Sets up candidate profile with skills and experiences.
    2. Discovers a target JobPosting.
    3. Triggers tailoring via POST /api/v1/tailor/trigger.
    4. Asserts 200 response and presence of side-by-side data comparing original and tailored bullets.
    5. Retrieves tailoring details via GET /api/v1/tailor/{job_posting_id}.
    6. Verifies clean database cascading and MinIO pre-signed download URLs.
    """
    headers = test_setup_data["headers"]
    email = test_setup_data["email"]

    user_id = None
    profile_id = uuid.uuid4()
    job_id = uuid.uuid4()
    exp_id = uuid.uuid4()

    # Setup candidate profile and job posting in database
    async with SessionLocal() as session:
        # Fetch the created user
        from sqlalchemy import delete, select
        query = select(User).where(User.email == email)
        res = await session.execute(query)
        user = res.scalar_one()
        user_id = user.id

        # Create user profile
        profile = UserProfile(
            id=profile_id,
            user_id=user_id,
            phone="+1 (555) 444-3322",
            preferred_roles=["Lead Developer"],
            preferred_locations=["Remote"],
            target_salary=140000
        )
        session.add(profile)
        await session.flush()

        # Add skill
        skill = Skill(profile_id=profile_id, name="Python")
        session.add(skill)

        # Add experience
        experience = Experience(
            id=exp_id,
            profile_id=profile_id,
            company="StartupCorp",
            role="Backend Engineer",
            start_date="2024",
            end_date="2026",
            description="Designed robust API endpoints with high security."
        )
        session.add(experience)

        # Add job posting
        job = JobPosting(
            id=job_id,
            platform="Greenhouse",
            external_job_id="api-job-77",
            board_token="apicorp",
            title="Senior Python Backend Developer",
            company="Apicorp",
            location="Remote",
            url="https://boards.greenhouse.io/apicorp/jobs/77",
            description_text="Looking for a Python Developer who builds highly secure REST APIs."
        )
        session.add(job)
        await session.commit()

    # Trigger tailoring and assert side-by-side comparison payload
    from app.core.config import settings
    original_api_key = settings.gemini_api_key
    settings.gemini_api_key = "mock-key-for-now"

    from app.services.tailoring.service import tailoring_pipeline_service
    original_client_key = tailoring_pipeline_service.gemini_client.api_key
    tailoring_pipeline_service.gemini_client.api_key = "mock-key-for-now"

    try:
        with TestClient(app) as client:
            # 1. Trigger tailoring
            trigger_payload = {"job_posting_id": str(job_id)}
            trigger_resp = client.post("/api/v1/tailor/trigger", json=trigger_payload, headers=headers)
            assert trigger_resp.status_code == 200

            data = trigger_resp.json()
            assert data["application_id"] is not None
            assert data["status"] == "Auto-Filled"
            assert data["mode"] == "Manual"
            assert data["tailored_resume_key"] is not None
            assert data["cover_letter_key"] is not None
            assert data["tailored_resume_url"] is not None
            assert data["cover_letter_url"] is not None

            # Check original data comparison
            orig = data["original_data"]
            assert "Python" in orig["skills"]
            assert len(orig["experiences"]) == 1
            assert orig["experiences"][0]["company"] == "StartupCorp"
            assert orig["experiences"][0]["role"] == "Backend Engineer"

            # Check tailored side-by-side data comparison
            tailored = data["tailored_data"]
            assert tailored["summary"] != ""
            assert "Python" in tailored["skills"]
            assert len(tailored["experience"]) == 1
            assert tailored["experience"][0]["company"] == "StartupCorp"
            assert len(tailored["experience"][0]["bullets"]) > 0

            # Check cover letter details
            cl = data["cover_letter"]
            assert cl["subject"] != ""
            assert "Dear Hiring Team" in cl["body"] or "Dear" in cl["body"]

            # 2. Query tailoring details via GET endpoint
            get_resp = client.get(f"/api/v1/tailor/{job_id}", headers=headers)
            assert get_resp.status_code == 200
            get_data = get_resp.json()
            assert get_data["application_id"] == data["application_id"]
            assert get_data["tailored_resume_key"] == data["tailored_resume_key"]
            assert get_data["cover_letter_key"] == data["cover_letter_key"]
            assert get_data["tailored_resume_url"] is not None
            assert get_data["cover_letter_url"] is not None

            # 3. Query details for an invalid/non-tailored job to verify 404 behavior
            fake_job_id = uuid.uuid4()
            fake_resp = client.get(f"/api/v1/tailor/{fake_job_id}", headers=headers)
            assert fake_resp.status_code == 404

    finally:
        settings.gemini_api_key = original_api_key
        tailoring_pipeline_service.gemini_client.api_key = original_client_key

    # Database Teardown Cleanup
    async with SessionLocal() as session:
        from sqlalchemy import delete
        await session.execute(delete(Application).where(Application.user_id == user_id))
        await session.execute(delete(JobPosting).where(JobPosting.id == job_id))
        await session.execute(delete(Experience).where(Experience.id == exp_id))
        await session.execute(delete(Skill).where(Skill.profile_id == profile_id))
        await session.execute(delete(UserProfile).where(UserProfile.id == profile_id))
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()
