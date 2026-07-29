import uuid
from unittest.mock import MagicMock, patch

import pytest
from app.domain.auth import User
from app.domain.job import JobPosting, MatchScore
from app.domain.profile import Skill, UserProfile
from app.infrastructure.db.session import SessionLocal
from app.main import app
from app.services.discovery.connector import GreenhouseConnector
from app.services.matching.scoring import job_matching_service
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

# --- MOCK API FEED RESPONSES ---

MOCK_GREENHOUSE_FEED = {
    "jobs": [
        {
            "id": 88801,
            "title": "Senior Python Developer",
            "absolute_url": "https://boards.greenhouse.io/testcorp/jobs/88801",
            "location": {"name": "Remote, US"},
            "content": "Full stack Python position. Offering $145,000 annually. Required skills: Python, FastAPI, Docker."
        },
        {
            "id": 88802,
            "title": "Frontend React developer",
            "absolute_url": "https://boards.greenhouse.io/testcorp/jobs/88802",
            "location": {"name": "New York, NY"},
            "content": "Looking for frontend React developer with 3+ years experience. Offering $110,000 annually."
        }
    ]
}

@pytest.fixture
def auth_headers():
    """Helper fixture to register a candidate, create their profile with matching target preferences, and return bearer tokens."""
    with TestClient(app) as client:
        test_id = uuid.uuid4().hex[:8]
        email = f"crawler_candidate_{test_id}@example.com"
        password = "SecurePassword123!"

        # 1. Register User
        reg_resp = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "first_name": "Crawler",
            "last_name": "Tester"
        })
        assert reg_resp.status_code == 201
        user_id = uuid.UUID(reg_resp.json()["id"])

        # 2. Login User
        login_resp = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        return {"Authorization": f"Bearer {token}", "user_id": user_id, "email": email}

@pytest.mark.asyncio
async def test_scheduled_discovery_lifecycle_integration(auth_headers):
    """
    Scheduled Discovery Lifecycle Integration Test:
    1. Populate the candidate's profile with matching targets (locations, preferred roles, salary, and skills).
    2. Execute simulated background Greenhouse discovery connectors crawler pings using mocked API payloads.
    3. Verify that 2 JobPostings are correctly parsed and saved into the database.
    4. Run JobMatchingService evaluations over all newly-added JobPostings, saving MatchScore breakdowns.
    5. Assert that jobs scoring above the configured threshold (e.g. 70) remain active, and those below are auto-archived.
    6. Execute re-runs of the connector to verify database deduplication.
    7. Query the `/api/v1/jobs` REST endpoint to confirm active listings are served correctly.
    8. Teardown and delete all database rows cleanly to prevent workspace pollution.
    """
    user_id = auth_headers["user_id"]
    headers = {"Authorization": auth_headers["Authorization"]}
    board_token = "integration_board_test"

    # Step 1: Initialize Candidate Profile
    async with SessionLocal() as session:
        profile_id = uuid.uuid4()
        profile = UserProfile(
            id=profile_id,
            user_id=user_id,
            phone="+1234567890",
            preferred_roles=["Senior Python Developer", "Backend Platform Engineer"],
            preferred_locations=["Remote", "Austin, TX"],
            target_salary=130000
        )
        session.add(profile)
        await session.flush()

        # Core skills used for matching comparisons
        skills = ["Python", "FastAPI", "Docker", "SQLAlchemy"]
        for skill_name in skills:
            skill = Skill(profile_id=profile_id, name=skill_name)
            session.add(skill)
        await session.commit()

    # Step 2: Trigger discovery crawler sync_board via GreenhouseConnector with mock payloads
    connector = GreenhouseConnector()
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_GREENHOUSE_FEED
        mock_get.return_value = mock_response

        # Execute first-time crawler sync
        async with SessionLocal() as session:
            jobs_synced = await connector.sync_board(session, board_token)
            assert len(jobs_synced) == 2

            job_ids = [j.id for j in jobs_synced]
            ext_ids = [j.external_job_id for j in jobs_synced]
            assert "88801" in ext_ids
            assert "88802" in ext_ids

    # Step 3: Run matching service evaluations over discovered jobs
    async with SessionLocal() as session:
        # Re-fetch profile and jobs for clean session states
        profile_query = await session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        db_profile = profile_query.scalar_one()

        for j_id in job_ids:
            job_query = await session.execute(
                select(JobPosting).where(JobPosting.id == j_id)
            )
            db_job = job_query.scalar_one()

            # Score each job
            await job_matching_service.score_and_evaluate_job(session, db_profile, db_job, threshold=70)

    # Step 4: Verify MatchScore outcomes and threshold rejections
    async with SessionLocal() as session:
        # Job 88801 (Senior Python Developer):
        # - Skills: Python, FastAPI, Docker match (3 out of 4 = 75% skills) -> 30 points
        # - Experience: matches preferred role -> 100% -> 30 points
        # - Location: "Remote, US" matches "Remote" -> 100% -> 15 points
        # - Salary: $145k matches target $130k -> 100% -> 15 points
        # Total overall score = 90% (exceeds threshold 70, is_archived = False)
        query_88801 = select(MatchScore).join(JobPosting).where(
            JobPosting.external_job_id == "88801",
            JobPosting.board_token == board_token
        )
        res_88801 = await session.execute(query_88801)
        score_88801 = res_88801.scalar_one()
        assert score_88801.overall_score == 90
        assert score_88801.is_archived is False

        # Job 88802 (Frontend React developer):
        # - Skills: 0 matches -> 0 points
        # - Experience: 0 matches -> 0 points
        # - Location: "New York, NY" does not match Dallas/Remote -> 0 points
        # - Salary: $110k is below target $130k (84% salary match) -> 12 points
        # Total overall score = 12% (below threshold 70, is_archived = True)
        query_88802 = select(MatchScore).join(JobPosting).where(
            JobPosting.external_job_id == "88802",
            JobPosting.board_token == board_token
        )
        res_88802 = await session.execute(query_88802)
        score_88802 = res_88802.scalar_one()
        assert score_88802.overall_score < 70
        assert score_88802.is_archived is True

    # Step 5: Re-run discovery connector crawler to verify DB deduplication
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_GREENHOUSE_FEED
        mock_get.return_value = mock_response

        async with SessionLocal() as session:
            jobs_synced_dup = await connector.sync_board(session, board_token)
            assert len(jobs_synced_dup) == 2

            # Assert no new records are added, verifying deduplication has occurred
            query_all = select(JobPosting).where(JobPosting.board_token == board_token)
            res_all = await session.execute(query_all)
            assert len(res_all.scalars().all()) == 2

    # Step 6: Query the REST endpoint to confirm active listings are served correctly
    with TestClient(app) as client:
        # Default endpoint query: should hide archived listings (< 70)
        resp_default = client.get("/api/v1/jobs", headers=headers)
        assert resp_default.status_code == 200
        data_default = resp_default.json()
        assert len(data_default) == 1
        assert data_default[0]["external_job_id"] == "88801"
        assert data_default[0]["match_score"]["overall_score"] == 90

        # Query with include_archived=true: should return both jobs
        resp_all = client.get("/api/v1/jobs?include_archived=true", headers=headers)
        assert resp_all.status_code == 200
        data_all = resp_all.json()
        assert len(data_all) == 2

    # Step 7: Teardown database structures (Clean-up)
    async with SessionLocal() as session:
        # Cascade deletes will clean up skill child rows
        await session.execute(delete(MatchScore).where(MatchScore.job_posting_id.in_(job_ids)))
        await session.execute(delete(JobPosting).where(JobPosting.id.in_(job_ids)))
        await session.execute(delete(UserProfile).where(UserProfile.id == profile_id))
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()
