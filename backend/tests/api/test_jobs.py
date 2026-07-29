import uuid

import pytest
from app.domain.job import JobPosting, MatchScore
from app.infrastructure.db.session import SessionLocal
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def auth_headers():
    """Helper fixture to create a random user and return their auth headers."""
    with TestClient(app) as client:
        email = f"jobs_candidate_{uuid.uuid4().hex[:8]}@example.com"
        password = "SecurePassword123!"

        # 1. Register
        register_payload = {
            "email": email,
            "password": password,
            "first_name": "Jobs",
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

@pytest.mark.asyncio
async def test_list_jobs_empty(auth_headers):
    """Verify that listing jobs returns an empty list initially when no jobs are present."""
    async with SessionLocal() as session:
        from sqlalchemy import delete
        await session.execute(delete(MatchScore))
        await session.execute(delete(JobPosting))
        await session.commit()

    with TestClient(app) as client:
        response = client.get("/api/v1/jobs", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

@pytest.mark.asyncio
async def test_list_jobs_with_scores(auth_headers):
    """Verify listing jobs returns populated list, with archiving logic working as expected."""
    async with SessionLocal() as session:
        from sqlalchemy import delete
        await session.execute(delete(MatchScore))
        await session.execute(delete(JobPosting))
        await session.commit()

    async with SessionLocal() as session:
        # 1. Create a non-archived job
        job_active = JobPosting(
            id=uuid.uuid4(),
            platform="Greenhouse",
            external_job_id="active-123",
            board_token="somecompany",
            title="Software Engineer",
            company="Some Company",
            location="Remote",
            url="http://example.com/job/active-123",
            description_text="FastAPI python description"
        )
        session.add(job_active)
        await session.flush()

        score_active = MatchScore(
            job_posting_id=job_active.id,
            overall_score=85,
            skill_score=90,
            experience_score=80,
            location_score=100,
            salary_score=80,
            is_archived=False
        )
        session.add(score_active)

        # 2. Create an archived job (score under 70)
        job_archived = JobPosting(
            id=uuid.uuid4(),
            platform="Lever",
            external_job_id="archived-999",
            board_token="somecompany",
            title="Product Designer",
            company="Some Company",
            location="New York",
            url="http://example.com/job/archived-999",
            description_text="Figma UX UI description"
        )
        session.add(job_archived)
        await session.flush()

        score_archived = MatchScore(
            job_posting_id=job_archived.id,
            overall_score=50,
            skill_score=40,
            experience_score=60,
            location_score=50,
            salary_score=60,
            is_archived=True
        )
        session.add(score_archived)

        await session.commit()

        active_id = job_active.id
        archived_id = job_archived.id

    try:
        with TestClient(app) as client:
            # Test default: should not include archived jobs
            response = client.get("/api/v1/jobs", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["external_job_id"] == "active-123"
            assert data[0]["match_score"]["overall_score"] == 85
            assert data[0]["match_score"]["is_archived"] is False

            # Test include_archived=True
            response_all = client.get("/api/v1/jobs?include_archived=true", headers=auth_headers)
            assert response_all.status_code == 200
            data_all = response_all.json()
            assert len(data_all) == 2
            ext_ids = [item["external_job_id"] for item in data_all]
            assert "active-123" in ext_ids
            assert "archived-999" in ext_ids

    finally:
        # Cleanup
        async with SessionLocal() as session:
            from sqlalchemy import delete
            await session.execute(delete(MatchScore).where(MatchScore.job_posting_id.in_([active_id, archived_id])))
            await session.execute(delete(JobPosting).where(JobPosting.id.in_([active_id, archived_id])))
            await session.commit()
