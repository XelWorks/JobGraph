import io
import os
import tempfile
import uuid

import pytest
from app.core.config import settings
from app.domain.auth import User
from app.domain.job import Application, JobPosting, MatchScore
from app.domain.profile import Experience, Skill, UserProfile
from app.infrastructure.browser.playwright_client import playwright_browser_core
from app.infrastructure.db.application_repository import application_repository
from app.infrastructure.db.profile_repository import profile_repository
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.storage.minio import storage
from app.services.applications.qa_agent import qa_agent_service
from app.services.matching.scoring import job_matching_service
from app.services.tailoring.service import tailoring_pipeline_service
from sqlalchemy import delete, select

MOCK_FULL_PIPELINE_FORM_HTML = """
<!DOCTYPE html>
<html>
<head><title>Full Pipeline Mock ATS Form</title></head>
<body>
  <form id="application_form" action="/submit" method="POST">
    <label for="first_name">First Name</label>
    <input type="text" id="first_name" name="job_application[first_name]" required />

    <label for="last_name">Last Name</label>
    <input type="text" id="last_name" name="job_application[last_name]" required />

    <label for="email">Email</label>
    <input type="email" id="email" name="job_application[email]" required />

    <label for="phone">Phone</label>
    <input type="text" id="phone" name="job_application[phone]" />

    <label for="resume_file">Resume Upload</label>
    <input type="file" id="resume_file" name="job_application[resume]" required />

    <label for="custom_q1">Years of Python experience:</label>
    <input type="text" id="custom_q1" name="custom_python_exp" />

    <button type="submit" id="submit_button">Submit Application</button>
  </form>
</body>
</html>
"""


@pytest.mark.asyncio
async def test_complete_end_to_end_application_flow():
    """
    Complete E2E Application Pipeline Integration Test:
    1. Register user & populate Candidate Profile with skills, experience & target criteria in DB.
    2. Upload master resume to MinIO object storage.
    3. Ingest a discovered JobPosting record (simulating Greenhouse ATS connector).
    4. Score and evaluate JobPosting using JobMatchingService (assert match_score >= 70).
    5. Run TailoringPipelineService to generate customized resume & cover letter PDFs and save to MinIO.
    6. Launch PlaywrightBrowserCore in Autonomous mode against local mock ATS page:
       - Autofills first/last name, email, phone.
       - Uploads the tailored resume PDF from MinIO.
       - Solves recruiter custom question using QAAgentService.
       - Clicks submit button.
    7. Update Application DB record to 'Submitted' with timestamp and notes.
    8. Assert all pipeline stages succeeded, files exist in S3, and DB state is 'Submitted'.
    9. Perform exhaustive database and MinIO storage cleanup (Teardown).
    """
    user_id = uuid.uuid4()
    profile_id = uuid.uuid4()
    exp_id = uuid.uuid4()
    job_id = uuid.uuid4()

    # Force mock API keys for offline testing
    original_api_key = settings.gemini_api_key
    settings.gemini_api_key = "mock-key-for-now"
    tailoring_pipeline_service.gemini_client.api_key = "mock-key-for-now"
    qa_agent_service.api_key = "mock-key-for-now"

    master_resume_key = None
    tailored_resume_key = None
    cover_letter_key = None
    app_id = None

    try:
        # --- STAGE 1: Setup Candidate Account & Profile ---
        async with SessionLocal() as session:
            user = User(
                id=user_id,
                email=f"e2e_flow_{user_id.hex[:8]}@example.com",
                hashed_password="hashed_password_123",
                first_name="E2E",
                last_name="FlowCandidate"
            )
            session.add(user)

            profile = UserProfile(
                id=profile_id,
                user_id=user_id,
                phone="+1 (555) 777-8888",
                preferred_roles=["Senior Python Engineer", "FastAPI Architect"],
                preferred_locations=["Remote"],
                target_salary=160000
            )
            session.add(profile)
            await session.flush()

            skill1 = Skill(profile_id=profile_id, name="Python")
            skill2 = Skill(profile_id=profile_id, name="FastAPI")
            skill3 = Skill(profile_id=profile_id, name="PostgreSQL")
            session.add_all([skill1, skill2, skill3])

            exp = Experience(
                id=exp_id,
                profile_id=profile_id,
                company="CloudScale Systems",
                role="Senior Python Engineer",
                start_date="2023",
                end_date="Present",
                description="Designed high-throughput async microservices using Python, FastAPI, and Postgres."
            )
            session.add(exp)
            await session.commit()

        # --- STAGE 2: Upload Master Resume to MinIO ---
        dummy_master_pdf = b"%PDF-1.4 Candidate Master Resume Payload"
        master_resume_key = f"resumes/{user_id}_master.pdf"
        storage.put_object(
            object_name=master_resume_key,
            data=io.BytesIO(dummy_master_pdf),
            length=len(dummy_master_pdf),
            content_type="application/pdf"
        )
        async with SessionLocal() as session:
            await profile_repository.update_resume_key(session, user_id, master_resume_key)

        # --- STAGE 3: Ingest Discovered Job Posting ---
        async with SessionLocal() as session:
            job = JobPosting(
                id=job_id,
                platform="Greenhouse",
                external_job_id="gh-e2e-101",
                board_token="scalecloud",
                title="Senior Python Engineer (FastAPI/Postgres)",
                company="ScaleCloud AI",
                location="Remote",
                url="https://boards.greenhouse.io/scalecloud/jobs/gh-e2e-101",
                description_text="We need a Senior Python Engineer with experience in FastAPI and Postgres. Offering $170,000 yearly."
            )
            session.add(job)
            await session.commit()

        # --- STAGE 4: Score & Evaluate Job Posting ---
        async with SessionLocal() as session:
            p_res = await session.execute(select(UserProfile).where(UserProfile.id == profile_id))
            db_profile = p_res.scalar_one()

            j_res = await session.execute(select(JobPosting).where(JobPosting.id == job_id))
            db_job = j_res.scalar_one()

            match_score = await job_matching_service.score_and_evaluate_job(session, db_profile, db_job, threshold=70)
            assert match_score.overall_score >= 70
            assert match_score.is_archived is False

        # --- STAGE 5: Tailor Resume & Cover Letter + Store in MinIO ---
        async with SessionLocal() as session:
            app_record = await tailoring_pipeline_service.generate_and_store_artifacts(
                db=session,
                user_id=user_id,
                job_posting_id=job_id
            )
            assert app_record.status == "Auto-Filled"
            assert app_record.tailored_resume_key is not None
            assert app_record.cover_letter_key is not None

            app_id = app_record.id
            tailored_resume_key = app_record.tailored_resume_key
            cover_letter_key = app_record.cover_letter_key

        # Verify tailored resume exists in MinIO
        resume_stat = storage.client.stat_object(storage.bucket_name, tailored_resume_key)
        assert resume_stat.size > 0

        # Download tailored resume bytes to temp file for Playwright upload
        resume_data_bytes = storage.client.get_object(storage.bucket_name, tailored_resume_key).read()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(resume_data_bytes)
            local_tailored_pdf_path = tmp_file.name

        # --- STAGE 6: Playwright Autonomous Form Execution against local HTML form ---
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f_html:
            f_html.write(MOCK_FULL_PIPELINE_FORM_HTML)
            local_html_form_path = f_html.name

        with tempfile.TemporaryDirectory() as screenshot_dir:
            screenshot_path = os.path.join(screenshot_dir, "e2e_submission.png")

            profile_dict = {
                "first_name": "E2E",
                "last_name": "FlowCandidate",
                "email": f"e2e_flow_{user_id.hex[:8]}@example.com",
                "phone": "+1 (555) 777-8888",
                "skills": ["Python", "FastAPI", "PostgreSQL"],
                "experiences": [{"company": "CloudScale Systems", "role": "Senior Python Engineer"}]
            }

            form_res = await playwright_browser_core.fill_application_form(
                url=f"file://{local_html_form_path}",
                profile_data=profile_dict,
                resume_path=local_tailored_pdf_path,
                screenshot_path=screenshot_path,
                mode="Autonomous"
            )

            assert form_res["status"] == "success"
            assert form_res["ats_type"] == "greenhouse"
            assert form_res["uploaded_resume"] is True
            assert form_res["custom_questions_answered"] >= 1
            assert form_res["submitted"] is True
            assert os.path.exists(screenshot_path)

        # Cleanup local temp files
        if os.path.exists(local_tailored_pdf_path):
            os.remove(local_tailored_pdf_path)
        if os.path.exists(local_html_form_path):
            os.remove(local_html_form_path)

        # --- STAGE 7: Update Application DB Record to 'Submitted' ---
        async with SessionLocal() as session:
            updated_app = await application_repository.update_artifacts(
                db=session,
                app_id=app_id,
                status="Submitted"
            )
            assert updated_app.status == "Submitted"

        # --- STAGE 8: Verify Complete DB Pipeline Integrity ---
        async with SessionLocal() as session:
            final_app = await application_repository.get_by_id(session, app_id)
            assert final_app is not None
            assert final_app.status == "Submitted"
            assert final_app.user_id == user_id
            assert final_app.job_posting_id == job_id
            assert final_app.tailored_resume_key == tailored_resume_key
            assert final_app.cover_letter_key == cover_letter_key

    finally:
        # Revert mock key settings
        settings.gemini_api_key = original_api_key
        tailoring_pipeline_service.gemini_client.api_key = original_api_key
        qa_agent_service.api_key = original_api_key

        # --- STAGE 9: Exhaustive Teardown & Resource Reset ---
        async with SessionLocal() as session:
            if app_id:
                await session.execute(delete(Application).where(Application.id == app_id))
            await session.execute(delete(MatchScore).where(MatchScore.job_posting_id == job_id))
            await session.execute(delete(JobPosting).where(JobPosting.id == job_id))
            await session.execute(delete(Experience).where(Experience.id == exp_id))
            await session.execute(delete(Skill).where(Skill.profile_id == profile_id))
            await session.execute(delete(UserProfile).where(UserProfile.id == profile_id))
            await session.execute(delete(User).where(User.id == user_id))
            await session.commit()

        # Remove MinIO objects
        for key in [master_resume_key, tailored_resume_key, cover_letter_key]:
            if key:
                try:
                    storage.client.remove_object(storage.bucket_name, key)
                except Exception as e:
                    print(f"S3 cleanup warning for {key}: {e}")
