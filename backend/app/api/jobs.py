import logging
import uuid
import json
import subprocess
import sys
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domain.auth import User
from app.domain.job import JobPosting, MatchScore
from app.domain.profile import UserProfile
from app.infrastructure.db.session import get_db
from app.infrastructure.db.vault_repository import vault_repository
from app.infrastructure.db.vault_repository import decrypt_payload
from app.services.discovery.connector import GreenhouseConnector, LeverConnector
from app.services.matching.scoring import job_matching_service

router = APIRouter()
logger = logging.getLogger("app.api.jobs")


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


async def _connected_portals_for_user(db: AsyncSession, user_id: uuid.UUID) -> set[str]:
    entries = await vault_repository.get_user_vault(db, user_id)
    return {entry.portal_name.strip().lower() for entry in entries if entry.portal_name}


async def _discover_browser_jobs(
    db: AsyncSession,
    user_id: uuid.UUID,
    portal: str,
    query: str,
    location: str,
) -> list[dict[str, Any]]:
    """Discover listings from a connected portal's saved browser profile."""
    entry = await vault_repository.get_portal_session(db, user_id, portal)
    if not entry or not entry.encrypted_session_payload:
        return []

    try:
        payload = json.loads(decrypt_payload(entry.encrypted_session_payload))
        profile_dir = payload.get("profile_dir") if isinstance(payload, dict) else None
    except (TypeError, ValueError):
        profile_dir = None
    if not profile_dir:
        return []

    helper = __import__("pathlib").Path(__file__).parents[1] / "services" / "discovery" / "browser_job_discovery.py"
    try:
        process = await __import__("asyncio").to_thread(
            subprocess.run,
            [sys.executable, str(helper), portal, profile_dir, query, location],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if process.returncode != 0:
        return []
    try:
        result = json.loads(process.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return []
    if isinstance(result, dict):
        if not result.get("jobs"):
            logger.warning(
                "browser_discovery_empty",
                extra={
                    "portal": portal,
                    "final_url": result.get("final_url"),
                    "page_title": result.get("page_title"),
                    "login_required": result.get("login_required"),
                },
            )
        return result.get("jobs", [])
    return []


def _seed_demo_jobs_for_portals(portals: set[str]) -> list[dict[str, Any]]:
    portal_jobs: list[dict[str, Any]] = []
    if "greenhouse" in portals:
        portal_jobs.append({
            "platform": "Greenhouse",
            "external_job_id": "demo-gh-101",
            "board_token": "demo-greenhouse",
            "title": "Senior Full-Stack Engineer",
            "company": "Northstar Labs",
            "location": "Remote",
            "url": "https://boards.greenhouse.io/demo-greenhouse/jobs/101",
            "description_text": "Build production systems, work across backend and frontend, and ship polished product experiences.",
            "match_score": {
                "overall_score": 92,
                "skill_score": 95,
                "experience_score": 88,
                "location_score": 100,
                "salary_score": 90,
                "is_archived": False,
            },
        })
    if "lever" in portals:
        portal_jobs.append({
            "platform": "Lever",
            "external_job_id": "demo-lever-202",
            "board_token": "demo-lever",
            "title": "Product Engineer",
            "company": "Signal Forge",
            "location": "San Francisco, CA",
            "url": "https://jobs.lever.co/demo-lever/202",
            "description_text": "Own product features end-to-end and drive rapid iteration with a strong software engineering mindset.",
            "match_score": {
                "overall_score": 85,
                "skill_score": 89,
                "experience_score": 82,
                "location_score": 80,
                "salary_score": 88,
                "is_archived": False,
            },
        })
    if "naukri" in portals:
        portal_jobs.append({
            "platform": "Naukri",
            "external_job_id": "demo-naukri-301",
            "board_token": "demo-naukri",
            "title": "Senior Python Engineer",
            "company": "TalentOrbit",
            "location": "Bengaluru, India",
            "url": "https://www.naukri.com/job-listings-senior-python-engineer-demo",
            "description_text": "Build backend services, APIs, and automation workflows for a local-first hiring platform.",
            "match_score": {
                "overall_score": 90,
                "skill_score": 94,
                "experience_score": 85,
                "location_score": 95,
                "salary_score": 85,
                "is_archived": False,
            },
        })
    return portal_jobs


@router.post("/discover", response_model=list[JobPostingResponse])
async def discover_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Populate the feed only from the portals the user has connected."""
    connected_portals = await _connected_portals_for_user(db, current_user.id)

    if connected_portals:
        existing = await db.execute(select(JobPosting))
        current_jobs = existing.scalars().all()
        existing_platforms = {job.platform.lower() for job in current_jobs}
        for portal in connected_portals:
            if portal not in existing_platforms:
                for job in _seed_demo_jobs_for_portals({portal}):
                    record = JobPosting(
                        platform=job["platform"],
                        external_job_id=job["external_job_id"],
                        board_token=job["board_token"],
                        title=job["title"],
                        company=job["company"],
                        location=job["location"],
                        url=job["url"],
                        description_text=job["description_text"],
                    )
                    db.add(record)
                    await db.flush()
                    score = job["match_score"]
                    db.add(
                        MatchScore(
                            job_posting_id=record.id,
                            overall_score=score["overall_score"],
                            skill_score=score["skill_score"],
                            experience_score=score["experience_score"],
                            location_score=score["location_score"],
                            salary_score=score["salary_score"],
                            is_archived=score["is_archived"],
                            evaluated_at=datetime.utcnow(),
                        )
                    )
        await db.commit()

    try:
        gh = GreenhouseConnector()
        lv = LeverConnector()
        for portal in connected_portals:
            if portal == "greenhouse":
                await gh.sync_board(db, "demo-greenhouse")
            if portal == "lever":
                await lv.sync_board(db, "demo-lever")
    except Exception:
        pass

    profile_query = "software engineer"
    profile_location = "remote"
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile:
        profile_query = (profile.preferred_roles or [profile_query])[0]
        profile_location = (profile.preferred_locations or [profile_location])[0]

    for portal in connected_portals & {"linkedin", "naukri", "glassdoor"}:
        for raw_job in await _discover_browser_jobs(db, current_user.id, portal, profile_query, profile_location):
            existing = await db.execute(select(JobPosting).where(JobPosting.url == raw_job["url"]))
            record = existing.scalar_one_or_none()
            if record:
                continue
            db.add(JobPosting(
                platform=portal.title(),
                external_job_id=raw_job["external_job_id"],
                board_token=portal,
                title=raw_job["title"][:255],
                company=raw_job["company"][:255],
                location=raw_job.get("location"),
                url=raw_job["url"][:1000],
                description_text=raw_job.get("description_text"),
            ))
    await db.commit()

    if profile:
        scored_jobs = await db.execute(select(JobPosting))
        for job in scored_jobs.scalars().all():
            if job.platform.lower() in connected_portals:
                await job_matching_service.score_and_evaluate_job(db, profile, job)

    jobs = await list_jobs(db=db, current_user=current_user, include_archived=True)
    return jobs


@router.get("", response_model=list[JobPostingResponse])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_archived: bool = Query(False, description="Include archived jobs"),
) -> Any:
    """
    Retrieve discovered job postings with their associated match scores.
    """
    query = select(JobPosting)
    result = await db.execute(query)
    jobs = result.scalars().all()

    connected_portals = await _connected_portals_for_user(db, current_user.id)
    if not connected_portals:
        return []

    jobs = [job for job in jobs if job.platform.lower() in connected_portals]

    filtered_jobs = []
    for job in jobs:
        if job.match_score:
            if not include_archived and job.match_score.is_archived:
                continue
        filtered_jobs.append(job)

    return filtered_jobs
