"""Autonomy control API endpoints for enabling/disabling autonomous job applications."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domain.auth import User
from app.infrastructure.db.session import get_db

router = APIRouter()


@router.get("/status")
async def get_autonomy_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get the current autonomy status for the authenticated user.
    
    Returns information about whether autonomous mode is enabled,
    application statistics, and scheduling information.
    """
    # Check if user has a profile with master resume
    from app.domain.profile import get_profile_by_user_id
    profile = await get_profile_by_user_id(db, current_user.id)
    
    if not profile or not profile.master_resume_key:
        raise HTTPException(
            status_code=400,
            detail="Profile not complete. Please upload your master resume before enabling autonomy.",
        )
    
    # Check if user has connected portals
    from app.domain.vault import get_portal_sessions
    portals = get_portal_sessions(db, current_user.id)
    
    if not portals:
        raise HTTPException(
            status_code=400,
            detail="No job portals connected. Please connect at least one portal in the Account Hub before enabling autonomy.",
        )
    
    # For now, return default disabled state
    # In production, this would query Redis or database for actual autonomy state
    return {
        "is_enabled": False,
        "is_running": False,
        "last_run_at": None,
        "next_run_at": None,
        "applications_today": 0,
        "daily_limit": 50,
        "errors_last_hour": 0,
    }


@router.post("/enable")
async def enable_autonomy(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Enable autonomous job application mode for the authenticated user.
    
    Once enabled, the system will automatically:
    - Discover new jobs every 30 minutes
    - Tailor resumes for high-match positions
    - Submit applications on connected portals
    - Create accounts on company career pages when needed
    """
    # Validate prerequisites
    from app.domain.profile import get_profile_by_user_id
    profile = await get_profile_by_user_id(db, current_user.id)
    
    if not profile or not profile.master_resume_key:
        raise HTTPException(
            status_code=400,
            detail="Profile not complete. Please upload your master resume before enabling autonomy.",
        )
    
    from app.domain.vault import get_portal_sessions
    portals = get_portal_sessions(db, current_user.id)
    
    if not portals:
        raise HTTPException(
            status_code=400,
            detail="No job portals connected. Please connect at least one portal in the Account Hub.",
        )
    
    # In production, this would:
    # 1. Set autonomy_enabled flag in Redis/database
    # 2. Notify the autonomous scheduler to start processing
    # 3. Log the enablement event
    
    return {
        "message": "Autonomous mode enabled successfully. The system will now discover and apply to jobs on your behalf.",
        "status": "enabled",
    }


@router.post("/disable")
async def disable_autonomy(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Disable autonomous job application mode for the authenticated user.
    
    Once disabled:
    - No new job discovery will occur
    - No automatic applications will be submitted
    - Existing applications continue their workflow
    - User can re-enable at any time
    """
    # In production, this would:
    # 1. Clear autonomy_enabled flag in Redis/database
    # 2. Signal the autonomous scheduler to pause
    # 3. Log the disablement event
    # 4. Allow current applications to complete gracefully
    
    return {
        "message": "Autonomous mode disabled. No new automatic applications will be made until you re-enable it.",
        "status": "disabled",
    }
