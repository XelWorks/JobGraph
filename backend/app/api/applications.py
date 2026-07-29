import logging
import uuid
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domain.auth import User
from app.domain.job import Application, JobPosting, MatchScore
from app.infrastructure.db.session import get_db
from app.infrastructure.storage.minio import storage

router = APIRouter()
logger = logging.getLogger("app.api.applications")


class JobCompactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    company: str
    location: Optional[str]
    url: str

class ApplicationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    job_posting_id: uuid.UUID
    status: str
    mode: str
    tailored_resume_key: Optional[str]
    cover_letter_key: Optional[str]
    tailored_resume_url: Optional[str]
    cover_letter_url: Optional[str]
    date_applied: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    job_posting: JobCompactResponse


class MetricBreakdown(BaseModel):
    overall_overall_avg: float
    total_found: int
    total_matched: int
    total_applied: int
    total_failed: int
    total_scheduled: int


class ApplicationUpdateStatusRequest(BaseModel):
    status: str
    notes: Optional[str] = None


@router.get("", response_model=List[ApplicationDetailResponse])
async def list_applications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve all applications initiated by the current user along with pre-signed document links.
    """
    # SQLAlchemy requires ordering
    query = select(Application).where(Application.user_id == current_user.id).order_by(Application.updated_at.desc())
    result = await db.execute(query)
    apps = result.scalars().all()

    response_apps = []
    for app_record in apps:
        resume_url = None
        if app_record.tailored_resume_key:
            try:
                resume_url = storage.get_presigned_url(app_record.tailored_resume_key)
            except Exception as e:
                logger.error(f"failed_presigned_resume_url: {e}")

        cover_url = None
        if app_record.cover_letter_key:
            try:
                cover_url = storage.get_presigned_url(app_record.cover_letter_key)
            except Exception as e:
                logger.error(f"failed_presigned_cover_url: {e}")

        # Construct response
        response_apps.append(
            ApplicationDetailResponse(
                id=app_record.id,
                user_id=app_record.user_id,
                job_posting_id=app_record.job_posting_id,
                status=app_record.status,
                mode=app_record.mode,
                tailored_resume_key=app_record.tailored_resume_key,
                cover_letter_key=app_record.cover_letter_key,
                tailored_resume_url=resume_url,
                cover_letter_url=cover_url,
                date_applied=app_record.date_applied,
                notes=app_record.notes,
                created_at=app_record.created_at,
                updated_at=app_record.updated_at,
                job_posting=JobCompactResponse(
                    id=app_record.job_posting.id,
                    title=app_record.job_posting.title,
                    company=app_record.job_posting.company,
                    location=app_record.job_posting.location,
                    url=app_record.job_posting.url
                )
            )
        )

    return response_apps


@router.get("/metrics", response_model=MetricBreakdown)
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Calculate and retrieve aggregate funnel performance metrics.
    """
    # 1. Total Job Postings Found
    jobs_query = select(JobPosting)
    jobs_res = await db.execute(jobs_query)
    total_found = len(jobs_res.scalars().all())

    # 2. Total Matched Job postings (overall match score >= 70)
    match_query = select(MatchScore).where(MatchScore.overall_score >= 70)
    match_res = await db.execute(match_query)
    total_matched = len(match_res.scalars().all())

    # 3. Calculate average overall score
    avg_query = select(MatchScore.overall_score)
    avg_res = await db.execute(avg_query)
    scores = avg_res.scalars().all()
    overall_avg = float(sum(scores) / len(scores)) if scores else 0.0

    # 4. Total Applications categorized by statuses
    app_query = select(Application).where(Application.user_id == current_user.id)
    app_res = await db.execute(app_query)
    apps = app_res.scalars().all()

    total_applied = sum(1 for a in apps if a.status in ["Submitted", "Auto-Filled"])
    total_failed = sum(1 for a in apps if a.status == "Failed")
    total_scheduled = sum(1 for a in apps if a.status == "Scheduled")

    return MetricBreakdown(
        overall_overall_avg=round(overall_avg, 2),
        total_found=total_found,
        total_matched=total_matched,
        total_applied=total_applied,
        total_failed=total_failed,
        total_scheduled=total_scheduled
    )


@router.patch("/{application_id}", response_model=ApplicationDetailResponse)
async def update_application_status(
    application_id: uuid.UUID,
    payload: ApplicationUpdateStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Updates the execution status or candidate notes of an application.
    """
    query = select(Application).where(Application.id == application_id, Application.user_id == current_user.id)
    res = await db.execute(query)
    app_record = res.scalar_one_or_none()
    if not app_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application tracking record not found."
        )

    # Validate status values
    allowed_statuses = ["Backlog", "Scheduled", "Auto-Filled", "Submitted", "Failed"]
    if payload.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status specified. Permitted: {allowed_statuses}"
        )

    app_record.status = payload.status
    if payload.notes is not None:
        app_record.notes = payload.notes

    if payload.status == "Submitted" and not app_record.date_applied:
        app_record.date_applied = datetime.utcnow()

    await db.commit()
    await db.refresh(app_record)

    resume_url = None
    if app_record.tailored_resume_key:
        try:
            resume_url = storage.get_presigned_url(app_record.tailored_resume_key)
        except Exception as e:
            logger.error(f"failed_presigned_resume_url: {e}")

    cover_url = None
    if app_record.cover_letter_key:
        try:
            cover_url = storage.get_presigned_url(app_record.cover_letter_key)
        except Exception as e:
            logger.error(f"failed_presigned_cover_url: {e}")

    return ApplicationDetailResponse(
        id=app_record.id,
        user_id=app_record.user_id,
        job_posting_id=app_record.job_posting_id,
        status=app_record.status,
        mode=app_record.mode,
        tailored_resume_key=app_record.tailored_resume_key,
        cover_letter_key=app_record.cover_letter_key,
        tailored_resume_url=resume_url,
        cover_letter_url=cover_url,
        date_applied=app_record.date_applied,
        notes=app_record.notes,
        created_at=app_record.created_at,
        updated_at=app_record.updated_at,
        job_posting=JobCompactResponse(
            id=app_record.job_posting.id,
            title=app_record.job_posting.title,
            company=app_record.job_posting.company,
            location=app_record.job_posting.location,
            url=app_record.job_posting.url
        )
    )
