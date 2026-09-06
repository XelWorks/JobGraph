import logging
from pathlib import Path
import tempfile
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
from app.infrastructure.db.profile_repository import profile_repository
from app.infrastructure.db.session import get_db
from app.infrastructure.storage.minio import storage
from app.infrastructure.db.vault_repository import decrypt_payload, vault_repository
from app.infrastructure.db.application_repository import application_repository
from app.services.applications.application_service import application_service

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


class ApplicationDispatchRequest(BaseModel):
    job_url: str
    resume_path: Optional[str] = None
    profile_data: dict[str, Any] = {}
    mode: str = "Autonomous"
    portal_name: Optional[str] = None
    session_payload: Optional[str] = None
    browser: str = "chrome"
    requires_review: bool = False


class ApplicationFromLinkRequest(BaseModel):
    job_url: str
    mode: str = "Autonomous"
    portal_name: Optional[str] = None
    requires_review: bool = False


def _portal_from_url(job_url: str) -> str:
    return application_service.infer_portal_name(job_url)


@router.post("/from-link", status_code=status.HTTP_202_ACCEPTED)
async def create_application_from_link(
    payload: ApplicationFromLinkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create and queue an application directly from a user-provided job URL."""
    job_url = payload.job_url.strip()
    if not job_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A valid http(s) job URL is required.")

    profile = await profile_repository.get_by_user_id(db, current_user.id)
    if not profile or not profile.master_resume_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload your master resume before starting an application.",
        )

    portal_name = application_service.infer_portal_name(job_url, payload.portal_name)
    portal_entry = await vault_repository.get_portal_session(db, current_user.id, portal_name)
    session_payload = None
    if portal_entry and portal_entry.encrypted_session_payload:
        session_payload = decrypt_payload(portal_entry.encrypted_session_payload)

    try:
        resume_bytes = storage.get_object_bytes(profile.master_resume_key)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded master resume could not be read. Upload it again before starting.",
        ) from exc

    with tempfile.NamedTemporaryFile(
        suffix=Path(profile.master_resume_key).suffix or ".pdf",
        delete=False,
    ) as resume_file:
        resume_file.write(resume_bytes)
        resume_path = resume_file.name

    job = JobPosting(
        platform=portal_name.title(),
        external_job_id=f"manual-{uuid.uuid4().hex}",
        board_token=portal_name,
        title="Application from provided link",
        company=portal_name.title(),
        location=None,
        url=job_url,
        description_text=None,
    )
    db.add(job)
    await db.flush()
    application = await application_repository.create_application(
        db,
        user_id=current_user.id,
        job_posting_id=job.id,
        mode=payload.mode,
        status="Scheduled",
        notes="Queued from user-provided job link. Login, OTP, MFA, or CAPTCHA may require user action in the browser.",
    )

    profile_data = {
        "first_name": current_user.first_name or "Candidate",
        "last_name": current_user.last_name or "Applicant",
        "email": current_user.email,
        "phone": profile.phone or "",
        "skills": [skill.name for skill in profile.skills],
    }
    await application_service.dispatch_application_task(
        application_id=application.id,
        job_url=job_url,
        profile_data=profile_data,
        resume_path=resume_path,
        mode=payload.mode,
        portal_name=portal_name,
        session_payload=session_payload,
        browser="chrome",
        requires_review=payload.requires_review,
    )
    return {
        "status": "queued",
        "application_id": str(application.id),
        "job_url": job_url,
        "portal_name": portal_name,
        "message": "Application queued. Complete any login, password, OTP, MFA, or CAPTCHA prompt in the opened browser.",
    }


@router.post("/{application_id}/dispatch", status_code=status.HTTP_202_ACCEPTED)
async def dispatch_application_for_job(
    application_id: uuid.UUID,
    payload: ApplicationDispatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Queue a real browser automation run for an existing application record."""
    query = select(Application).where(Application.id == application_id, Application.user_id == current_user.id)
    result = await db.execute(query)
    app_record = result.scalar_one_or_none()
    if not app_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application tracking record not found.",
        )

    job_url = payload.job_url.strip()
    if not job_url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid http(s) job URL is required.",
        )

    profile = await profile_repository.get_by_user_id(db, current_user.id)
    portal_name = application_service.infer_portal_name(job_url, payload.portal_name)
    portal_entry = await vault_repository.get_portal_session(db, current_user.id, portal_name)
    session_payload = payload.session_payload
    if not session_payload and portal_entry and portal_entry.encrypted_session_payload:
        try:
            session_payload = decrypt_payload(portal_entry.encrypted_session_payload)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The {portal_name} browser profile cannot be read. Reconnect the portal.",
            ) from exc
    resolved_profile_data = dict(payload.profile_data or {})
    if profile:
        if not resolved_profile_data.get("first_name"):
            resolved_profile_data["first_name"] = (current_user.first_name or "Candidate")
        if not resolved_profile_data.get("last_name"):
            resolved_profile_data["last_name"] = (current_user.last_name or "Applicant")
        if not resolved_profile_data.get("email"):
            resolved_profile_data["email"] = current_user.email
        if not resolved_profile_data.get("phone") and profile.phone:
            resolved_profile_data["phone"] = profile.phone
        if not resolved_profile_data.get("skills") and profile.skills:
            resolved_profile_data["skills"] = [skill.name for skill in profile.skills]

    resume_path = payload.resume_path
    if not resume_path and app_record.tailored_resume_key:
        try:
            local_pdf = storage.get_object_bytes(app_record.tailored_resume_key)
        except Exception as exc:
            logger.warning(
                "tailored_resume_missing_or_unreadable",
                extra={
                    "application_id": str(app_record.id),
                    "resume_key": app_record.tailored_resume_key,
                    "error": str(exc),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The tailored resume for this application is missing or unreadable. Upload or regenerate the resume before dispatching.",
            ) from exc

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(local_pdf)
            resume_path = temp_file.name

    if not resume_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tailored resume is available for this application. Please generate the resume first.",
        )

    await application_service.dispatch_application_task(
        application_id=app_record.id,
        job_url=job_url,
        profile_data=resolved_profile_data,
        resume_path=resume_path,
        mode=payload.mode,
        portal_name=portal_name,
        session_payload=session_payload,
        browser=payload.browser,
        requires_review=payload.requires_review,
    )

    return {
        "status": "queued",
        "application_id": str(app_record.id),
        "job_url": job_url,
        "portal_name": application_service.infer_portal_name(job_url, payload.portal_name),
        "mode": payload.mode,
    }


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
