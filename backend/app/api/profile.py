import io
import logging
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domain.auth import User
from app.infrastructure.db.profile_repository import profile_repository
from app.infrastructure.db.session import get_db
from app.infrastructure.storage.minio import storage

router = APIRouter()
logger = logging.getLogger(__name__)

class ProfileCreateUpdate(BaseModel):
    phone: str | None = Field(None, description="Phone number")
    preferred_roles: list[str] | None = Field(None, description="Preferred roles")
    preferred_locations: list[str] | None = Field(None, description="Preferred locations")
    target_salary: int | None = Field(None, ge=0, description="Target salary (must be non-negative)")
    skills: list[str] = Field(..., description="List of skills")

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v: list[str]) -> list[str]:
        cleaned = [s.strip() for s in v if s.strip()]
        if not cleaned:
            raise ValueError("Skills list cannot be empty.")
        return cleaned

class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    phone: str | None
    master_resume_url: str | None = None
    preferred_roles: list[str] | None = None
    preferred_locations: list[str] | None = None
    target_salary: int | None = None
    skills: list[str] = []

@router.post("", response_model=ProfileResponse)
async def create_or_update_profile(
    payload: ProfileCreateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update candidate profile."""
    try:
        profile = await profile_repository.save_profile(
            db=db,
            user_id=current_user.id,
            phone=payload.phone,
            preferred_roles=payload.preferred_roles,
            preferred_locations=payload.preferred_locations,
            target_salary=payload.target_salary,
            skills=payload.skills
        )

        # Build response with presigned URL
        resume_url = None
        if profile.master_resume_key:
            resume_url = storage.get_presigned_url(profile.master_resume_key)

        return ProfileResponse(
            user_id=profile.user_id,
            phone=profile.phone,
            master_resume_url=resume_url,
            preferred_roles=profile.preferred_roles,
            preferred_locations=profile.preferred_locations,
            target_salary=profile.target_salary,
            skills=[s.name for s in profile.skills]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e

@router.get("", response_model=ProfileResponse)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve current candidate profile."""
    profile = await profile_repository.get_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found."
        )

    resume_url = None
    if profile.master_resume_key:
        resume_url = storage.get_presigned_url(profile.master_resume_key)

    return ProfileResponse(
        user_id=profile.user_id,
        phone=profile.phone,
        master_resume_url=resume_url,
        preferred_roles=profile.preferred_roles,
        preferred_locations=profile.preferred_locations,
        target_salary=profile.target_salary,
        skills=[s.name for s in profile.skills]
    )

@router.post("/resume", response_model=ProfileResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload master PDF/Docx resume to MinIO and map to candidate profile."""
    filename = file.filename or "resume.pdf"
    ext = filename.split(".")[-1].lower()
    if ext not in ["pdf", "docx", "doc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF or Word documents (.docx, .doc) are permitted."
        )

    # Read payload bytes
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded."
        )

    object_name = f"resumes/{current_user.id}_{uuid.uuid4().hex[:8]}_{filename}"

    # Put to MinIO
    try:
        storage.put_object(
            object_name=object_name,
            data=io.BytesIO(file_bytes),
            length=len(file_bytes),
            content_type=file.content_type or "application/octet-stream"
        )
    except Exception as e:
        logger.error(f"failed_to_save_resume_to_minio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to storage."
        ) from e

    # Link to DB profile
    profile = await profile_repository.update_resume_key(
        db=db,
        user_id=current_user.id,
        resume_key=object_name
    )

    resume_url = storage.get_presigned_url(profile.master_resume_key)

    return ProfileResponse(
        user_id=profile.user_id,
        phone=profile.phone,
        master_resume_url=resume_url,
        preferred_roles=profile.preferred_roles,
        preferred_locations=profile.preferred_locations,
        target_salary=profile.target_salary,
        skills=[s.name for s in profile.skills]
    )
