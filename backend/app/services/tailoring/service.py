import logging
import os
import tempfile
import uuid

from app.domain.auth import User
from app.domain.job import Application, JobPosting
from app.infrastructure.db.application_repository import application_repository
from app.infrastructure.db.profile_repository import profile_repository
from app.infrastructure.storage.artifacts import save_cover_letter, save_tailored_resume
from app.services.tailoring.gemini import GeminiClient, generate_pdf_cover_letter, generate_pdf_resume
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("app.services.tailoring.service")

class TailoringPipelineService:
    """Service to orchestrate the retrieval, tailoring, PDF compilation, and secure storage of resume and cover letter artifacts."""

    def __init__(self) -> None:
        self.gemini_client = GeminiClient()

    async def generate_and_store_artifacts(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        job_posting_id: uuid.UUID
    ) -> Application:
        """
        Orchestrates full tailoring pipeline:
        1. Fetch Candidate User and Profile.
        2. Fetch target Job Posting.
        3. Initialize or retrieve the Application record.
        4. Request resume tailoring and compile to PDF.
        5. Request cover letter tailoring and compile to PDF.
        6. Store both files securely in MinIO with UUID nonces.
        7. Update application state and artifact links in database.
        """
        # 1. Fetch User
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User with ID {user_id} does not exist.")

        # 2. Fetch User Profile
        profile = await profile_repository.get_by_user_id(db, user_id)
        if not profile:
            raise ValueError("Candidate profile must be configured before tailoring documents.")

        # 3. Fetch Job Posting
        job_query = select(JobPosting).where(JobPosting.id == job_posting_id)
        job_result = await db.execute(job_query)
        job = job_result.scalar_one_or_none()
        if not job:
            raise ValueError(f"Job posting with ID {job_posting_id} does not exist.")

        # 4. Check/Create Application Record
        application = await application_repository.get_by_user_and_job(db, user_id, job_posting_id)
        if not application:
            application = await application_repository.create_application(
                db,
                user_id=user_id,
                job_posting_id=job_posting_id,
                mode="Manual",
                status="Backlog"
            )

        # 5. Extract and format candidate info
        candidate_info = {
            "first_name": user.first_name or "Candidate",
            "last_name": user.last_name or "Account",
            "email": user.email,
            "phone": profile.phone or "",
            "skills": [s.name for s in profile.skills],
            "experiences": [
                {
                    "company": exp.company,
                    "role": exp.role,
                    "start_date": exp.start_date,
                    "end_date": exp.end_date,
                    "description": exp.description
                }
                for exp in profile.experiences
            ]
        }

        # 6. Generate tailored resume details and compile to PDF
        logger.info(f"Generating tailored resume for application {application.id}")
        resume_data = await self.gemini_client.generate_tailored_resume_data(
            candidate_info=candidate_info,
            job_title=job.title,
            job_company=job.company,
            job_description=job.description_text or ""
        )

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_resume:
            tmp_resume_path = tmp_resume.name

        try:
            generate_pdf_resume(resume_data, tmp_resume_path)
            with open(tmp_resume_path, "rb") as f:
                resume_bytes = f.read()
        finally:
            if os.path.exists(tmp_resume_path):
                os.remove(tmp_resume_path)

        # 7. Generate tailored cover letter details and compile to PDF
        logger.info(f"Generating tailored cover letter for application {application.id}")
        cover_letter_data = await self.gemini_client.generate_tailored_cover_letter_data(
            candidate_info=candidate_info,
            job_title=job.title,
            job_company=job.company,
            job_description=job.description_text or ""
        )

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_cl:
            tmp_cl_path = tmp_cl.name

        try:
            generate_pdf_cover_letter(cover_letter_data, tmp_cl_path)
            with open(tmp_cl_path, "rb") as f:
                cl_bytes = f.read()
        finally:
            if os.path.exists(tmp_cl_path):
                os.remove(tmp_cl_path)

        # 8. Upload documents securely to MinIO
        resume_key = save_tailored_resume(application.id, resume_bytes)
        cover_letter_key = save_cover_letter(application.id, cl_bytes)

        # 9. Link files and update state in DB
        updated_app = await application_repository.update_artifacts(
            db,
            app_id=application.id,
            resume_key=resume_key,
            cover_letter_key=cover_letter_key,
            status="Auto-Filled",
            resume_data=resume_data,
            cover_letter_data=cover_letter_data
        )

        logger.info(f"Tailored documents successfully generated and stored for application {application.id}")
        return updated_app

tailoring_pipeline_service = TailoringPipelineService()
