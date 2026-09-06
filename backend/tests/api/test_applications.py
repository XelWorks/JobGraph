import uuid
from unittest.mock import AsyncMock, patch

import pytest
from app.domain.auth import User
from app.domain.job import Application, JobPosting, MatchScore
from app.infrastructure.db.session import SessionLocal
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def auth_headers():
    """Helper fixture to create a random user and return their auth headers and email."""
    with TestClient(app) as client:
        email = f"app_tester_{uuid.uuid4().hex[:8]}@example.com"
        password = "SecurePassword123!"

        # 1. Register
        register_payload = {
            "email": email,
            "password": password,
            "first_name": "Apps",
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

        return {"Authorization": f"Bearer {token}"}, email


@pytest.mark.asyncio
async def test_applications_tracking_api(auth_headers):
    """
    Test Applications Tracking API endpoints:
    1. Verify list is empty.
    2. Add standard JobPosting, MatchScore, and Application records.
    3. Verify /api/v1/applications lists the tracking records with pre-signed document hooks.
    4. Verify /api/v1/applications/metrics calculates aggregate counts.
    5. Verify PATCH /api/v1/applications/{id} updates statuses and notes correctly.
    6. Teardown cleanly.
    """
    headers, email = auth_headers
    user_id = None
    job_id = uuid.uuid4()
    app_id = uuid.uuid4()

    # Get User ID
    async with SessionLocal() as session:
        from sqlalchemy import select
        u_query = select(User).where(User.email == email)
        u_res = await session.execute(u_query)
        user = u_res.scalar_one()
        user_id = user.id

    # 1. Check empty
    with TestClient(app) as client:
        response = client.get("/api/v1/applications", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

    # 2. Insert records
    async with SessionLocal() as session:
        job = JobPosting(
            id=job_id,
            platform="Greenhouse",
            external_job_id="ext-abc-11",
            board_token="testcorp",
            title="SRE Engineer",
            company="Testcorp",
            location="Remote",
            url="https://jobs.testcorp.com/sre"
        )
        session.add(job)
        await session.flush()

        score = MatchScore(
            job_posting_id=job_id,
            overall_score=85,
            skill_score=80,
            experience_score=90,
            location_score=100,
            salary_score=70
        )
        session.add(score)

        application = Application(
            id=app_id,
            user_id=user_id,
            job_posting_id=job_id,
            status="Scheduled",
            mode="Assisted",
            tailored_resume_key="resumes/fake_key.pdf",
            cover_letter_key="cover_letters/fake_key.pdf",
            notes="Ready to run."
        )
        session.add(application)
        await session.commit()

    # 3. Check listing with documents
    with TestClient(app) as client:
        response = client.get("/api/v1/applications", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(app_id)
        assert data[0]["status"] == "Scheduled"
        assert data[0]["mode"] == "Assisted"
        assert data[0]["tailored_resume_url"] is not None
        assert data[0]["cover_letter_url"] is not None
        assert data[0]["job_posting"]["title"] == "SRE Engineer"
        assert data[0]["job_posting"]["company"] == "Testcorp"

        # 4. Check metrics aggregations
        metrics_resp = client.get("/api/v1/applications/metrics", headers=headers)
        assert metrics_resp.status_code == 200
        metrics = metrics_resp.json()
        assert metrics["total_found"] >= 1
        assert metrics["total_matched"] >= 1
        assert metrics["total_scheduled"] == 1
        assert metrics["total_applied"] == 0
        assert metrics["overall_overall_avg"] > 0

        # 5. Check PATCH update status
        patch_payload = {
            "status": "Submitted",
            "notes": "Submitted successfully through Assisted mode!"
        }
        patch_resp = client.patch(f"/api/v1/applications/{app_id}", json=patch_payload, headers=headers)
        assert patch_resp.status_code == 200
        patch_data = patch_resp.json()
        assert patch_data["status"] == "Submitted"
        assert patch_data["notes"] == "Submitted successfully through Assisted mode!"
        assert patch_data["date_applied"] is not None

        # Verify update reflected in metrics
        metrics_resp2 = client.get("/api/v1/applications/metrics", headers=headers)
        assert metrics_resp2.json()["total_applied"] == 1
        assert metrics_resp2.json()["total_scheduled"] == 0

    # 6. Teardown
    async with SessionLocal() as session:
        from sqlalchemy import delete
        await session.execute(delete(Application).where(Application.id == app_id))
        await session.execute(delete(MatchScore).where(MatchScore.job_posting_id == job_id))
        await session.execute(delete(JobPosting).where(JobPosting.id == job_id))
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()


@pytest.mark.asyncio
async def test_dispatch_application_queue_uses_tailored_resume(auth_headers):
    headers, email = auth_headers
    user_id = None
    job_id = uuid.uuid4()
    app_id = uuid.uuid4()

    async with SessionLocal() as session:
        from sqlalchemy import select
        user = (await session.execute(select(User).where(User.email == email))).scalar_one()
        user_id = user.id

        job = JobPosting(
            id=job_id,
            platform="Greenhouse",
            external_job_id="dispatch-123",
            board_token="dispatch-board",
            title="Platform Engineer",
            company="Dispatch Co",
            location="Remote",
            url="https://boards.greenhouse.io/dispatch-board/jobs/123",
            description_text="Build distributed systems",
        )
        session.add(job)
        await session.flush()

        application = Application(
            id=app_id,
            user_id=user_id,
            job_posting_id=job_id,
            status="Scheduled",
            mode="Autonomous",
            tailored_resume_key="resumes/test-tailored.pdf",
        )
        session.add(application)
        await session.commit()

    with patch("app.infrastructure.queue.valkey_queue.AsyncRedis") as MockAsyncRedis, patch(
        "app.infrastructure.storage.minio.storage.get_object_bytes",
        return_value=b"%PDF-1.4\nmock resume",
    ):
        mock_client = AsyncMock()
        mock_client.rpush = AsyncMock()
        MockAsyncRedis.from_url.return_value = mock_client

        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/applications/{app_id}/dispatch",
                json={
                    "job_url": "https://boards.greenhouse.io/dispatch-board/jobs/123",
                    "profile_data": {"first_name": "Dispatch", "last_name": "Tester"},
                    "mode": "Autonomous",
                    "portal_name": "greenhouse",
                },
                headers=headers,
            )

        assert response.status_code == 202
        assert response.json()["status"] == "queued"
        assert mock_client.rpush.await_count == 1

    async with SessionLocal() as session:
        from sqlalchemy import delete
        await session.execute(delete(Application).where(Application.id == app_id))
        await session.execute(delete(JobPosting).where(JobPosting.id == job_id))
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()
