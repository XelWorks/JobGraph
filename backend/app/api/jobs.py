import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domain.auth import User
from app.domain.job import JobPosting
from app.infrastructure.db.session import get_db

router = APIRouter()


class MatchScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    overall_score: int
    skill_score: int
    experience_score: int
    location_score: int
    salary_score: int
    is_archived: bool
    evaluated_at: datetime


class JobPostingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    platform: str
    external_job_id: str
    board_token: str
    title: str
    company: str
    location: str | None
    url: str
    description_text: str | None
    discovered_at: datetime
    match_score: MatchScoreResponse | None = None


@router.get("", response_model=list[JobPostingResponse])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_archived: bool = Query(False, description="Include archived jobs"),
) -> Any:
    """
    Retrieve discovered job postings with their associated match scores.
    """
    # Fetch job postings and join with match scores if exists
    query = select(JobPosting)

    result = await db.execute(query)
    jobs = result.scalars().all()

    # Filter based on match score archived status if required
    filtered_jobs = []
    for job in jobs:
        if job.match_score:
            if not include_archived and job.match_score.is_archived:
                continue
        filtered_jobs.append(job)

    return filtered_jobs
