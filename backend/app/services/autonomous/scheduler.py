"""
Autonomous Job Application Scheduler

This module provides continuous background job discovery and application functionality,
enabling the system to work autonomously on behalf of the user even when they're away.

Features:
- Continuous job discovery from multiple portals
- Automated resume tailoring for each job
- Intelligent application scheduling with rate limiting
- Session management and refresh
- Retry logic with exponential backoff
- Daily progress reports
"""
import asyncio
import logging
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.domain.job import Application, JobPosting
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.profile_repository import profile_repository
from app.infrastructure.db.application_repository import application_repository
from app.infrastructure.db.vault_repository import vault_repository, decrypt_payload
from app.services.applications.application_service import application_service
from app.services.discovery.browser_job_discovery import search_url
from app.services.tailoring.service import tailoring_pipeline_service as tailoring_service
from app.services.automation.events import event_bus, ApplicationStarted, StatusSaved

logger = logging.getLogger("app.services.autonomous.scheduler")


class AutonomousScheduler:
    """
    Main scheduler class for autonomous job discovery and application.
    
    This scheduler runs continuously in the background, discovering jobs,
    tailoring resumes, and submitting applications based on user preferences.
    """
    
    def __init__(self) -> None:
        self.running = False
        self._shutdown_event = asyncio.Event()
        self._last_application_time: Dict[str, datetime] = {}  # Per-user rate limiting
        self._daily_application_count: Dict[str, int] = {}  # Per-user daily counts
        self._last_reset_date: str = ""
        self._retry_counts: Dict[str, int] = {}  # Track retry attempts per application
        
    async def start(self) -> None:
        """Start the autonomous scheduler."""
        if not settings.autonomous_mode_enabled:
            logger.warning("autonomous_mode_disabled")
            return
            
        self.running = True
        logger.info("autonomous_scheduler_started")
        
        try:
            await self._main_loop()
        except asyncio.CancelledError:
            logger.info("autonomous_scheduler_cancelled")
        except Exception as e:
            logger.error(f"autonomous_scheduler_crashed: {e}")
            raise
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the scheduler."""
        logger.info("autonomous_scheduler_shutting_down")
        self.running = False
        self._shutdown_event.set()
        logger.info("autonomous_scheduler_shutdown_complete")
    
    async def _main_loop(self) -> None:
        """Main scheduling loop that orchestrates discovery and application."""
        logger.info("autonomous_scheduler_main_loop_started")
        
        while self.running:
            try:
                # Reset daily counters if new day
                await self._reset_daily_counters_if_needed()
                
                # Get all active users with profiles
                async with SessionLocal() as session:
                    # For now, we'll process all users with complete profiles
                    # In production, this would query a user preferences table
                    users_to_process = await self._get_active_users(session)
                
                for user_id, user_data in users_to_process.items():
                    if not self.running:
                        break
                        
                    # Check daily limit
                    if not self._can_apply_more_today(user_id):
                        logger.info(
                            "daily_limit_reached",
                            extra={"user_id": user_id, "count": self._daily_application_count.get(user_id, 0)}
                        )
                        continue
                    
                    # Check rate limiting between applications
                    if not self._respect_rate_limit(user_id):
                        logger.info("rate_limit_active", extra={"user_id": user_id})
                        await asyncio.sleep(settings.application_interval_seconds)
                        continue
                    
                    # Discover new jobs
                    jobs = await self._discover_jobs(user_data)
                    
                    if jobs:
                        # Process each discovered job
                        for job in jobs:
                            if not self.running:
                                break
                                
                            if not self._can_apply_more_today(user_id):
                                break
                            
                            # Check if already applied
                            if await self._already_applied(job["url"], user_id):
                                continue
                            
                            # Tailor resume
                            tailored_resume_path = await self._tailor_resume_for_job(
                                job, user_data
                            )
                            
                            if tailored_resume_path:
                                # Create application record
                                application_id = await self._create_application_record(
                                    job, user_id, tailored_resume_path
                                )
                                
                                if application_id:
                                    # Dispatch application task
                                    success = await self._dispatch_application(
                                        application_id, job, user_data, tailored_resume_path
                                    )
                                    
                                    if success:
                                        self._record_application(user_id)
                                    
                                    # Rate limit between applications
                                    await asyncio.sleep(settings.application_interval_seconds)
                    
                # Wait before next discovery cycle
                await asyncio.sleep(settings.job_discovery_interval_seconds)
                
            except asyncio.CancelledError:
                logger.info("scheduler_loop_cancelled")
                break
            except Exception as e:
                logger.error(f"scheduler_loop_error: {e}")
                await asyncio.sleep(60)  # Wait before retrying on error
    
    async def _get_active_users(self, session: Any) -> Dict[str, Dict[str, Any]]:
        """Get all active users with complete profiles ready for autonomous application."""
        # This is a placeholder - in production, query user preferences
        # For now, we'll return a structure that can be populated from DB
        users = {}
        
        # Query users with complete profiles and autonomous mode enabled
        # This would typically join User, UserProfile, and a hypothetical UserPreferences table
        try:
            from sqlalchemy import select
            from app.domain.auth import User
            from app.domain.profile import UserProfile
            
            result = await session.execute(
                select(User).join(UserProfile, User.id == UserProfile.user_id)
                .where(UserProfile.master_resume_key.isnot(None))
            )
            db_users = result.scalars().all()
            
            for user in db_users:
                profile = await profile_repository.get_by_user_id(session, user.id)
                if profile and profile.master_resume_key:
                    users[str(user.id)] = {
                        "user_id": str(user.id),
                        "email": user.email,
                        "first_name": user.first_name or "",
                        "last_name": user.last_name or "",
                        "profile": profile,
                    }
        except Exception as e:
            logger.error(f"error_fetching_users: {e}")
        
        return users
    
    async def _discover_jobs(self, user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover new jobs from configured portals."""
        jobs = []
        profile = user_data.get("profile")
        
        if not profile:
            return jobs
        
        # Extract search criteria from profile
        # In production, this would come from user preferences
        search_queries = [
            ("linkedin", "software engineer", "remote"),
            ("linkedin", "software developer", "remote"),
            ("naukri", "software engineer", "Bangalore"),
            ("glassdoor", "software engineer", "remote"),
        ]
        
        for portal, query, location in search_queries:
            try:
                # Get portal session if available
                async with SessionLocal() as session:
                    user_id = uuid.UUID(user_data["user_id"])
                    portal_session = await vault_repository.get_portal_session(
                        session, user_id, portal
                    )
                    session_payload = None
                    if portal_session and portal_session.encrypted_session_payload:
                        session_payload = decrypt_payload(portal_session.encrypted_session_payload)
                
                # Use browser-based discovery (runs in visible browser)
                # This is more reliable than API scraping
                import subprocess
                import sys
                import json
                from pathlib import Path
                
                profile_dir = None
                if session_payload:
                    try:
                        import json as json_lib
                        payload_data = json_lib.loads(session_payload)
                        if isinstance(payload_data, dict):
                            profile_dir = payload_data.get("profile_dir")
                    except Exception:
                        pass
                
                if not profile_dir:
                    profile_dir = str(Path.home() / ".chrome_profiles" / portal)
                
                script_path = Path(__file__).parent.parent / "services" / "discovery" / "browser_job_discovery.py"
                
                # Use xvfb-run for headless execution in server environments
                import shutil
                use_xvfb = shutil.which("xvfb-run") is not None
                
                cmd = [sys.executable, str(script_path), portal, profile_dir, query, location]
                if use_xvfb:
                    cmd = ["xvfb-run", "-a"] + cmd
                
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=90)
                
                if proc.returncode == 0:
                    result = json.loads(stdout.decode())
                    discovered_jobs = result.get("jobs", [])
                    jobs.extend(discovered_jobs)
                    logger.info(
                        "jobs_discovered",
                        extra={"portal": portal, "count": len(discovered_jobs)}
                    )
                
            except NotImplementedError as nie:
                # This shouldn't happen - log full traceback for debugging
                import traceback
                logger.error(
                    f"job_discovery_not_implemented_{portal}: {nie}",
                    extra={"traceback": traceback.format_exc()}
                )
            except Exception as e:
                logger.error(f"job_discovery_failed_{portal}: {e}")
        
        return jobs
    
    async def _tailor_resume_for_job(
        self, job: Dict[str, Any], user_data: Dict[str, Any]
    ) -> Optional[str]:
        """Tailor resume for a specific job."""
        try:
            profile = user_data.get("profile")
            if not profile:
                return None
            
            async with SessionLocal() as session:
                user_id = uuid.UUID(user_data["user_id"])
                
                # Get master resume
                from app.infrastructure.storage.minio import storage
                resume_bytes = storage.get_object_bytes(profile.master_resume_key)
                
                # Create temporary file for tailoring
                import tempfile
                from pathlib import Path
                
                with tempfile.NamedTemporaryFile(
                    suffix=Path(profile.master_resume_key).suffix or ".pdf",
                    delete=False,
                ) as temp_file:
                    temp_file.write(resume_bytes)
                    master_resume_path = temp_file.name
                
                # Fetch job description if URL provided
                job_description = job.get("description_text", "")
                if not job_description and job.get("url"):
                    # In production, fetch job description from URL
                    job_description = await self._fetch_job_description(job["url"])
                
                # Tailor resume using AI
                tailored_result = await tailoring_service.tailor_resume(
                    master_resume_path=master_resume_path,
                    job_description=job_description,
                    job_title=job.get("title", ""),
                    company=job.get("company", ""),
                    candidate_profile={
                        "first_name": user_data.get("first_name", ""),
                        "last_name": user_data.get("last_name", ""),
                        "email": user_data.get("email", ""),
                        "skills": [s.name for s in profile.skills] if profile.skills else [],
                    }
                )
                
                # Save tailored resume
                if tailored_result.get("tailored_resume_path"):
                    return tailored_result["tailored_resume_path"]
                
        except Exception as e:
            logger.error(f"resume_tailoring_failed: {e}")
        
        return None
    
    async def _fetch_job_description(self, job_url: str) -> str:
        """Fetch job description from URL."""
        # Placeholder - in production, use Playwright to scrape job page
        return ""
    
    async def _create_application_record(
        self, job: Dict[str, Any], user_id: str, resume_path: str
    ) -> Optional[uuid.UUID]:
        """Create application tracking record in database."""
        try:
            async with SessionLocal() as session:
                user_uuid = uuid.UUID(user_id)
                
                # Create job posting if doesn't exist
                job_posting = JobPosting(
                    platform=job.get("company", "Unknown"),
                    external_job_id=job.get("external_job_id", f"auto-{uuid.uuid4().hex}"),
                    board_token=job.get("company", "").lower(),
                    title=job.get("title", "Unknown Position"),
                    company=job.get("company", "Unknown Company"),
                    location=job.get("location", "Remote"),
                    url=job.get("url", ""),
                    description_text=job.get("description_text", ""),
                )
                session.add(job_posting)
                await session.flush()
                
                # Store tailored resume in MinIO
                from app.infrastructure.storage.minio import storage
                from pathlib import Path
                
                object_key = f"resumes/{user_id}/{uuid.uuid4().hex}.pdf"
                with open(resume_path, "rb") as f:
                    await storage.upload_file(object_key, f.read())
                
                # Create application record
                application = await application_repository.create_application(
                    session,
                    user_id=user_uuid,
                    job_posting_id=job_posting.id,
                    mode="Autonomous",
                    status="Scheduled",
                    notes="Auto-generated application by autonomous scheduler",
                    tailored_resume_key=object_key,
                )
                
                await session.commit()
                
                logger.info(
                    "application_record_created",
                    extra={"application_id": str(application.id), "job_url": job.get("url")}
                )
                
                return application.id
                
        except Exception as e:
            logger.error(f"application_creation_failed: {e}")
            return None
    
    async def _dispatch_application(
        self,
        application_id: uuid.UUID,
        job: Dict[str, Any],
        user_data: Dict[str, Any],
        resume_path: str,
    ) -> bool:
        """Dispatch application task to browser worker."""
        try:
            job_url = job.get("url", "")
            if not job_url:
                return False
            
            profile = user_data.get("profile")
            profile_data = {
                "first_name": user_data.get("first_name", "Candidate"),
                "last_name": user_data.get("last_name", "Applicant"),
                "email": user_data.get("email", ""),
                "phone": profile.phone if profile else "",
                "skills": [s.name for s in profile.skills] if profile and profile.skills else [],
                "user_id": user_data["user_id"],  # Critical for account creation
            }
            
            # Get portal session
            portal_name = application_service.infer_portal_name(job_url)
            session_payload = None
            
            async with SessionLocal() as session:
                user_id = uuid.UUID(user_data["user_id"])
                portal_entry = await vault_repository.get_portal_session(
                    session, user_id, portal_name
                )
                if portal_entry and portal_entry.encrypted_session_payload:
                    session_payload = decrypt_payload(portal_entry.encrypted_session_payload)
            
            # Dispatch to queue
            await application_service.dispatch_application_task(
                application_id=application_id,
                job_url=job_url,
                profile_data=profile_data,
                resume_path=resume_path,
                mode="Autonomous",
                portal_name=portal_name,
                session_payload=session_payload,
                browser="chrome",
                requires_review=portal_name in {"linkedin", "naukri", "glassdoor"},
            )
            
            logger.info(
                "application_dispatched",
                extra={"application_id": str(application_id), "portal": portal_name}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"application_dispatch_failed: {e}")
            return False
    
    def _can_apply_more_today(self, user_id: str) -> bool:
        """Check if user hasn't exceeded daily application limit."""
        today = datetime.utcnow().date().isoformat()
        
        if self._last_reset_date != today:
            self._daily_application_count.clear()
            self._last_reset_date = today
        
        current_count = self._daily_application_count.get(user_id, 0)
        return current_count < settings.max_applications_per_day
    
    def _record_application(self, user_id: str) -> None:
        """Record an application for rate limiting."""
        self._daily_application_count[user_id] = self._daily_application_count.get(user_id, 0) + 1
        self._last_application_time[user_id] = datetime.utcnow()
    
    def _respect_rate_limit(self, user_id: str) -> bool:
        """Check if enough time has passed since last application."""
        last_time = self._last_application_time.get(user_id)
        if not last_time:
            return True
        
        elapsed = (datetime.utcnow() - last_time).total_seconds()
        return elapsed >= settings.application_interval_seconds
    
    async def _reset_daily_counters_if_needed(self) -> None:
        """Reset daily counters at midnight UTC."""
        today = datetime.utcnow().date().isoformat()
        if self._last_reset_date != today:
            self._daily_application_count.clear()
            self._last_reset_date = today
            logger.info("daily_counters_reset")
    
    async def _already_applied(self, job_url: str, user_id: str) -> bool:
        """Check if user has already applied to this job."""
        try:
            async with SessionLocal() as session:
                user_uuid = uuid.UUID(user_id)
                # Check existing applications
                from sqlalchemy import select
                result = await session.execute(
                    select(Application)
                    .join(JobPosting)
                    .where(
                        Application.user_id == user_uuid,
                        JobPosting.url == job_url
                    )
                )
                existing = result.scalar_one_or_none()
                return existing is not None
        except Exception as e:
            logger.error(f"check_existing_application_failed: {e}")
            return False


# Singleton instance
autonomous_scheduler = AutonomousScheduler()


async def start_autonomous_scheduler() -> None:
    """Convenience function to start the autonomous scheduler."""
    await autonomous_scheduler.start()
