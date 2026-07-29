import os
import tempfile
import uuid

import pytest
from app.domain.auth import User
from app.domain.job import Application, JobPosting
from app.domain.profile import Experience, Skill, UserProfile
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.storage.minio import storage
from app.services.tailoring.gemini import generate_pdf_cover_letter
from app.services.tailoring.service import tailoring_pipeline_service
from sqlalchemy import delete


@pytest.mark.asyncio
async def test_cover_letter_pdf_generation():
    """Unit test to verify ReportLab cover letter PDF compiles cleanly."""
    cover_letter_data = {
        "subject": "Staff Engineer Application",
        "body": "Dear Hiring Team,\n\nI am writing to apply...\n\nSincerely,\nCandidate"
    }
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_cl:
        tmp_path = tmp_cl.name
    try:
        generate_pdf_cover_letter(cover_letter_data, tmp_path)
        assert os.path.exists(tmp_path)
        assert os.path.getsize(tmp_path) > 0
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@pytest.mark.asyncio
async def test_full_tailoring_and_artifact_storage_integration():
    """
    Integration Test for Story 4.2:
    1. Setup user, profile, experience, skills, and a job posting in the DB.
    2. Execute `tailoring_pipeline_service.generate_and_store_artifacts`.
    3. Assert that an Application record is created/reused.
    4. Assert that Application has status 'Auto-Filled'.
    5. Assert that tailored_resume_key and cover_letter_key are generated.
    6. Verify that files exist in MinIO and are non-empty.
    7. Tear down user, profile, experiences, job, and MinIO artifacts cleanly.
    """
    user_id = uuid.uuid4()
    profile_id = uuid.uuid4()
    job_id = uuid.uuid4()
    exp_id = uuid.uuid4()

    # 1. Setup Data
    async with SessionLocal() as session:
        user = User(
            id=user_id,
            email=f"tailor_tester_{user_id.hex[:8]}@example.com",
            hashed_password="hashed_password",
            first_name="Tailor",
            last_name="Tester"
        )
        session.add(user)

        profile = UserProfile(
            id=profile_id,
            user_id=user_id,
            phone="+1 (555) 019-2834",
            preferred_roles=["Senior AI Engineer"],
            preferred_locations=["Remote"],
            target_salary=150000
        )
        session.add(profile)
        await session.flush()

        skill = Skill(profile_id=profile_id, name="Generative AI")
        session.add(skill)

        experience = Experience(
            id=exp_id,
            profile_id=profile_id,
            company="InnovateLLM",
            role="Machine Learning Engineer",
            start_date="2025",
            end_date="Present",
            description="Built custom search embeddings and agentic workflows."
        )
        session.add(experience)

        job = JobPosting(
            id=job_id,
            platform="Lever",
            external_job_id="lever-101",
            board_token="levercorp",
            title="AI Solutions Architect",
            company="Levercorp",
            location="Remote",
            url="https://lever.co/levercorp/jobs/lever-101",
            description_text="Seeking an AI Architect with experience in Generative AI and agentic workflows."
        )
        session.add(job)
        await session.commit()

    # 2. Run Pipeline
    from app.core.config import settings
    original_api_key = settings.gemini_api_key
    settings.gemini_api_key = "mock-key-for-now"

    original_client_key = tailoring_pipeline_service.gemini_client.api_key
    tailoring_pipeline_service.gemini_client.api_key = "mock-key-for-now"

    try:
        async with SessionLocal() as session:
            app_record = await tailoring_pipeline_service.generate_and_store_artifacts(
                db=session,
                user_id=user_id,
                job_posting_id=job_id
            )
    finally:
        settings.gemini_api_key = original_api_key
        tailoring_pipeline_service.gemini_client.api_key = original_client_key

    # 3. Assertions on Application model
    assert app_record is not None
    assert app_record.user_id == user_id
    assert app_record.job_posting_id == job_id
    assert app_record.status == "Auto-Filled"
    assert app_record.mode == "Manual"
    assert app_record.tailored_resume_key is not None
    assert app_record.cover_letter_key is not None

    # Verify nonces / path prefixes to prevent directory traversal
    assert "resumes/" in app_record.tailored_resume_key
    assert "cover_letters/" in app_record.cover_letter_key

    # 4. Verify MinIO files
    # Check files exist in MinIO bucket
    exists = storage.client.bucket_exists(storage.bucket_name)
    assert exists is True

    resume_stat = storage.client.stat_object(storage.bucket_name, app_record.tailored_resume_key)
    cl_stat = storage.client.stat_object(storage.bucket_name, app_record.cover_letter_key)

    assert resume_stat.size > 0
    assert cl_stat.size > 0
    assert resume_stat.content_type == "application/pdf"
    assert cl_stat.content_type == "application/pdf"

    # Keep track of object keys for cleanup
    resume_key = app_record.tailored_resume_key
    cl_key = app_record.cover_letter_key
    application_id = app_record.id

    # 5. Clean up
    async with SessionLocal() as session:
        # Delete models
        await session.execute(delete(Application).where(Application.id == application_id))
        await session.execute(delete(JobPosting).where(JobPosting.id == job_id))
        await session.execute(delete(Experience).where(Experience.id == exp_id))
        await session.execute(delete(Skill).where(Skill.profile_id == profile_id))
        await session.execute(delete(UserProfile).where(UserProfile.id == profile_id))
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()

    # Delete storage objects
    try:
        storage.client.remove_object(storage.bucket_name, resume_key)
        storage.client.remove_object(storage.bucket_name, cl_key)
    except Exception as e:
        print(f"Cleanup storage objects warning: {e}")
