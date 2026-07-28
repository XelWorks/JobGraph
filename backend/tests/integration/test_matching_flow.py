import uuid
import pytest
from sqlalchemy import select, delete

from app.main import app
from app.domain.auth import User
from app.domain.profile import UserProfile, Skill
from app.domain.job import JobPosting, MatchScore
from app.infrastructure.db.session import SessionLocal
from app.services.matching.scoring import job_matching_service

@pytest.mark.asyncio
async def test_full_job_matching_ingestion_integration():
    """
    Integration Test:
    1. Register user and create candidate profile with skills and target criteria.
    2. Insert a sample JobPosting record representing Greenhouse discovered listing.
    3. Execute service scoring to calculate MatchScore breakdowns and threshold rejections.
    4. Assert MatchScore is persisted securely inside matching tables with correct weights.
    5. Re-run scoring to test MatchScore record updates and deduplications.
    6. Teardown and delete all database insertions cleanly.
    """
    user_id = uuid.uuid4()
    profile_record_id = uuid.uuid4()
    job_id = uuid.uuid4()
    
    async with SessionLocal() as session:
        # Create test User
        user = User(
            id=user_id,
            email=f"matching_tester_{user_id.hex[:8]}@example.com",
            hashed_password="hashed_password",
            first_name="Matching",
            last_name="Tester"
        )
        session.add(user)
        
        # Create test UserProfile
        profile = UserProfile(
            id=profile_record_id,
            user_id=user_id,
            phone="+1234567890",
            preferred_roles=["Senior Python Engineer", "Backend Developer"],
            preferred_locations=["Remote", "Austin, TX"],
            target_salary=130000
        )
        session.add(profile)
        await session.flush()
        
        # Add profile skills
        skills = ["Python", "FastAPI", "PostgreSQL", "Docker"]
        for skill_name in skills:
            skill = Skill(profile_id=profile_record_id, name=skill_name)
            session.add(skill)
            
        # Create JobPosting listing
        job = JobPosting(
            id=job_id,
            platform="Greenhouse",
            external_job_id="9999",
            board_token="testcorp",
            title="Senior Python Engineer (FastAPI/Postgres)",
            company="Testcorp",
            location="Remote, US",
            url="https://boards.greenhouse.io/testcorp/jobs/9999",
            description_text="We need a Senior Python Engineer experienced in FastAPI, Postgres, and Docker. Offering $140,000 yearly."
        )
        session.add(job)
        await session.commit()

    # Re-fetch objects for clean session run
    async with SessionLocal() as session:
        profile_query = await session.execute(
            select(UserProfile).where(UserProfile.id == profile_record_id)
        )
        db_profile = profile_query.scalar_one()
        
        job_query = await session.execute(
            select(JobPosting).where(JobPosting.id == job_id)
        )
        db_job = job_query.scalar_one()
        
        # Execute Matching service
        # Expected Score breakdown weights:
        # - Skill: Python, FastAPI, PostgreSQL (mapped to Postgres), Docker matches = 100% matched -> 40 points
        # - Experience: "Senior Python Engineer" matches "Senior Python Engineer" preferred role -> 100% -> 30 points
        # - Location: "Remote, US" matches "Remote" preference -> 100% -> 15 points
        # - Salary: $140,000 matches or exceeds $130,000 target -> 100% -> 15 points
        # Overall expected score = 100
        match_score = await job_matching_service.score_and_evaluate_job(session, db_profile, db_job, threshold=70)
        
        assert match_score.overall_score == 100
        assert match_score.skill_score == 100
        assert match_score.experience_score == 100
        assert match_score.location_score == 100
        assert match_score.salary_score == 100
        assert match_score.is_archived is False
        
        # Re-run scoring to test deduplication in update-mode
        # Temporarily increase threshold to 110 to trigger auto-archiving
        updated_score = await job_matching_service.score_and_evaluate_job(session, db_profile, db_job, threshold=110)
        assert updated_score.id == match_score.id
        assert updated_score.is_archived is True

        # Assert query returns exactly one match score
        query = select(MatchScore).where(MatchScore.job_posting_id == job_id)
        res = await session.execute(query)
        match_scores = res.scalars().all()
        assert len(match_scores) == 1

        # Clean up database insertions (Teardown)
        await session.execute(delete(MatchScore).where(MatchScore.job_posting_id == job_id))
        await session.execute(delete(JobPosting).where(JobPosting.id == job_id))
        await session.execute(delete(UserProfile).where(UserProfile.id == profile_record_id))
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()
