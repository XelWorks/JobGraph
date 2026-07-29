import logging
import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domain.auth import User
from app.domain.job import Application, JobPosting
from app.infrastructure.db.application_repository import application_repository
from app.infrastructure.db.profile_repository import profile_repository
from app.infrastructure.db.session import get_db
from app.infrastructure.storage.minio import storage
from app.services.tailoring.service import tailoring_pipeline_service

router = APIRouter()
logger = logging.getLogger("app.api.tailor")

class TailorTriggerRequest(BaseModel):
    job_posting_id: uuid.UUID

class ExperienceItemOriginal(BaseModel):
    company: str
    role: str
    dates: str
    description: str | None

class OriginalData(BaseModel):
    skills: List[str]
    experiences: List[ExperienceItemOriginal]

class ExperienceItemTailored(BaseModel):
    company: str
    role: str
    dates: str
    bullets: List[str]

class TailoredData(BaseModel):
    summary: str
    skills: List[str]
    experience: List[ExperienceItemTailored]

class CoverLetterData(BaseModel):
    subject: str
    body: str

class TailorDetailResponse(BaseModel):
    application_id: uuid.UUID
    status: str
    mode: str
    tailored_resume_key: str | None
    cover_letter_key: str | None
    tailored_resume_url: str | None
    cover_letter_url: str | None
    original_data: OriginalData
    tailored_data: TailoredData | None
    cover_letter: CoverLetterData | None

def build_tailor_response(user: User, profile: Any, job: JobPosting, app_record: Application) -> TailorDetailResponse:
    # 1. Format original data
    original_experiences = []
    for exp in (profile.experiences or []):
        dates = f"{exp.start_date or ''} - {exp.end_date or ''}".strip(" -")
        original_experiences.append(
            ExperienceItemOriginal(
                company=exp.company,
                role=exp.role,
                dates=dates,
                description=exp.description
            )
        )
    original_data = OriginalData(
        skills=[s.name for s in (profile.skills or [])],
        experiences=original_experiences
    )

    # 2. Format tailored data if exists
    tailored_data = None
    if app_record.tailored_resume_data:
        tr_data = app_record.tailored_resume_data
        tailored_experiences = []
        for exp in tr_data.get("experience", []):
            tailored_experiences.append(
                ExperienceItemTailored(
                    company=exp.get("company", ""),
                    role=exp.get("role", ""),
                    dates=exp.get("dates", ""),
                    bullets=exp.get("bullets", [])
                )
            )
        tailored_data = TailoredData(
            summary=tr_data.get("summary", ""),
            skills=tr_data.get("skills", []),
            experience=tailored_experiences
        )

    # 3. Format cover letter if exists
    cover_letter = None
    if app_record.tailored_cover_letter_data:
        tcl_data = app_record.tailored_cover_letter_data
        cover_letter = CoverLetterData(
            subject=tcl_data.get("subject", ""),
            body=tcl_data.get("body", "")
        )

    # 4. Generate secure pre-signed download URLs valid for 15 minutes
    resume_url = None
    if app_record.tailored_resume_key:
        try:
            resume_url = storage.get_presigned_url(app_record.tailored_resume_key)
        except Exception as e:
            logger.error(f"failed_to_get_presigned_resume_url: {e}")

    cover_letter_url = None
    if app_record.cover_letter_key:
        try:
            cover_letter_url = storage.get_presigned_url(app_record.cover_letter_key)
        except Exception as e:
            logger.error(f"failed_to_get_presigned_cover_letter_url: {e}")

    return TailorDetailResponse(
        application_id=app_record.id,
        status=app_record.status,
        mode=app_record.mode,
        tailored_resume_key=app_record.tailored_resume_key,
        cover_letter_key=app_record.cover_letter_key,
        tailored_resume_url=resume_url,
        cover_letter_url=cover_letter_url,
        original_data=original_data,
        tailored_data=tailored_data,
        cover_letter=cover_letter,
    )

@router.post("/trigger", response_model=TailorDetailResponse)
async def trigger_tailoring(
    request: TailorTriggerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Triggers Gemini-based resume tailoring and cover letter generation, compiles PDFs,
    uploads to MinIO securely, links to database, and returns the side-by-side payloads & pre-signed links.
    """
    try:
        # 1. Generate & store artifacts
        app_record = await tailoring_pipeline_service.generate_and_store_artifacts(
            db=db,
            user_id=current_user.id,
            job_posting_id=request.job_posting_id
        )

        # 2. Get profile and job posting
        profile = await profile_repository.get_by_user_id(db, current_user.id)
        job_query = select(JobPosting).where(JobPosting.id == request.job_posting_id)
        job_res = await db.execute(job_query)
        job = job_res.scalar_one()

        return build_tailor_response(current_user, profile, job, app_record)

    except ValueError as e:
        logger.error(f"tailoring_trigger_failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"tailoring_trigger_unexpected_error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error running the tailoring pipeline. Please check LLM keys."
        ) from e

@router.get("/{job_posting_id}", response_model=TailorDetailResponse)
async def get_tailoring_details(
    job_posting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Fetches custom pre-signed URLs and side-by-side data comparing original and tailored results.
    """
    # 1. Fetch Application Record
    app_record = await application_repository.get_by_user_and_job(db, current_user.id, job_posting_id)
    if not app_record or not app_record.tailored_resume_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tailored artifacts exist yet for this job listing. Please trigger tailoring first."
        )

    # 2. Fetch Profile & Job Posting
    profile = await profile_repository.get_by_user_id(db, current_user.id)
    job_query = select(JobPosting).where(JobPosting.id == job_posting_id)
    job_res = await db.execute(job_query)
    job = job_res.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found."
        )

    return build_tailor_response(current_user, profile, job, app_record)
