"""Application service for dispatching browser automation tasks to Valkey queue."""
import logging
import uuid
from typing import Any

from app.infrastructure.queue.valkey_queue import ValkeyQueue

logger = logging.getLogger(__name__)


class ApplicationService:
    """
    Service for managing application submission workflows.
    
    Dispatches browser automation tasks to the Valkey queue for
    asynchronous processing by the standalone browser worker.
    """

    def __init__(self) -> None:
        self.queue = ValkeyQueue()

    @staticmethod
    def infer_portal_name(job_url: str, portal_name: str | None = None) -> str:
        """Infer a portal name from a job URL when the caller does not supply one."""
        normalized = (portal_name or "").strip().lower()
        if normalized:
            return normalized

        lower_url = (job_url or "").lower()
        if "linkedin.com" in lower_url:
            return "linkedin"
        if "naukri.com" in lower_url:
            return "naukri"
        if "glassdoor.com" in lower_url:
            return "glassdoor"
        if "greenhouse.io" in lower_url:
            return "greenhouse"
        if "lever.co" in lower_url:
            return "lever"
        return "unknown"

    async def dispatch_application_task(
        self,
        application_id: uuid.UUID,
        job_url: str,
        profile_data: dict[str, Any],
        resume_path: str,
        mode: str = "Autonomous",
        portal_name: str | None = None,
        session_payload: str | None = None,
        browser: str = "chrome",
        requires_review: bool = False,
    ) -> None:
        """
        Dispatch an application task to the Valkey queue for background processing.

        Includes portal/session metadata so the browser worker can operate in a
        Chrome-based human-like flow and track the run against the target portal.
        """
        task_payload = {
            "application_id": str(application_id),
            "job_url": job_url,
            "profile_data": profile_data,
            "resume_path": resume_path,
            "mode": mode,
            "portal_name": self.infer_portal_name(job_url, portal_name),
            "session_payload": session_payload,
            "browser": browser,
            "requires_review": requires_review,
            "tracking_status": "Tracked",
        }

        await self.queue.push_task("application", task_payload)

        logger.info(
            "application_task_dispatched",
            extra={
                "application_id": str(application_id),
                "job_url": job_url,
                "mode": mode
            }
        )

    async def close(self) -> None:
        """Close queue connection."""
        await self.queue.close()


# Singleton instance
application_service = ApplicationService()
