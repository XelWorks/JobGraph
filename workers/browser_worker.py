#!/usr/bin/env python3
"""
Standalone Browser Worker Daemon

Long-running worker process that polls Valkey queue for application tasks
and executes Playwright browser automation in an isolated process.

Usage:
    python workers/browser_worker.py
"""
import asyncio
import logging
import os
import signal
import sys
import json
from pathlib import Path
from typing import Any

# Add backend to Python path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.config import settings
from app.domain.auth import User  # noqa: F401
from app.domain.job import Application
from app.infrastructure.browser.playwright_client import PlaywrightBrowserCore
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.queue.valkey_queue import ValkeyQueue
from app.services.automation.browser_runtime import PortalAutomationRuntime
from app.services.automation.events import (
    ApplicationStarted,
    ApplicationSubmitted,
    SessionValidated,
    StatusSaved,
    WorkerAssigned,
    event_bus,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("workers.browser_worker")


class BrowserWorker:
    """
    Standalone browser worker daemon that consumes application tasks from Valkey
    and executes Playwright automation in isolation from the FastAPI web server.
    """

    def __init__(self) -> None:
        self.queue = ValkeyQueue()
        self.browser_core = PlaywrightBrowserCore(
            headless=False,
            default_timeout_ms=30000
        )
        self.running = False
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Start the worker daemon and begin polling for tasks."""
        self.running = True
        logger.info("browser_worker_started", extra={"worker_id": os.getpid()})

        # Register signal handlers for graceful shutdown when the platform supports them.
        # Windows does not support add_signal_handler on the default event loop, so we
        # simply skip it there and rely on the main thread's KeyboardInterrupt path.
        loop = asyncio.get_event_loop()
        if hasattr(loop, "add_signal_handler"):
            for sig in (signal.SIGTERM, signal.SIGINT):
                try:
                    loop.add_signal_handler(
                        sig,
                        lambda s=sig: asyncio.create_task(self._handle_shutdown(s))
                    )
                except (NotImplementedError, OSError):
                    logger.info(
                        "signal_handlers_not_supported_on_platform",
                        extra={"platform": sys.platform, "signal": sig.name},
                    )
                    break

        try:
            await self._poll_loop()
        except Exception as e:
            logger.error(
                "worker_crashed",
                extra={"error": str(e), "error_type": type(e).__name__}
            )
            raise
        finally:
            await self.shutdown()

    async def _poll_loop(self) -> None:
        """Main polling loop that consumes tasks from Valkey queue."""
        logger.info("worker_polling_started")

        while self.running:
            try:
                # Block for up to 5 seconds waiting for a task
                task = await self.queue.pop_task("application", timeout=5)

                if task is None:
                    # No task available, continue polling
                    continue

                logger.info(
                    "task_received",
                    extra={
                        "application_id": task.get("application_id"),
                        "job_url": task.get("job_url")
                    }
                )

                # Execute the task
                await self._execute_task(task)

            except asyncio.CancelledError:
                logger.info("worker_poll_cancelled")
                break
            except Exception as e:
                logger.exception(
                    "task_execution_error",
                    extra={"error": str(e), "error_type": type(e).__name__}
                )
                # Continue polling even if one task fails
                await asyncio.sleep(1)

    async def _execute_task(self, task: dict[str, Any]) -> None:
        """
        Execute a single application task using Playwright browser automation.
        
        Args:
            task: Task payload containing application_id, job_url, profile_data, resume_path
        """
        application_id = task.get("application_id")
        job_url = task.get("job_url")
        profile_data = task.get("profile_data", {})
        resume_path = task.get("resume_path")
        mode = task.get("mode", "Autonomous")
        portal_name = task.get("portal_name") or "unknown"
        session_payload = task.get("session_payload")
        requires_review = bool(task.get("requires_review", False))

        if not job_url or not resume_path:
            logger.error(
                "invalid_task_payload",
                extra={
                    "application_id": application_id,
                    "missing_fields": [
                        k for k in ["job_url", "resume_path"]
                        if not task.get(k)
                    ]
                }
            )
            return

        logger.info(
            "task_execution_started",
            extra={
                "application_id": application_id,
                "job_url": job_url,
                "mode": mode
            }
        )

        try:
            await self._save_application_status(
                application_id,
                "Auto-Filled",
                "Browser worker started the application flow.",
            )
            # Execute Playwright browser automation
            runtime = PortalAutomationRuntime(
                portal_name=str(portal_name),
                session_payload=session_payload,
            )
            profile_dir = None
            if session_payload:
                try:
                    session_data = json.loads(session_payload)
                    if isinstance(session_data, dict):
                        profile_dir = session_data.get("profile_dir")
                except (TypeError, ValueError):
                    logger.warning("invalid_browser_profile_payload", extra={"portal": portal_name})
            execution_plan = runtime.build_execution_plan(
                application_id=str(application_id),
                job_url=job_url,
                user_data_dir=profile_dir,
            )
            browser_context = execution_plan["browser"]

            await event_bus.emit(WorkerAssigned(
                application_id=str(application_id),
                worker_id=str(os.getpid()),
            ))
            await event_bus.emit(ApplicationStarted(
                application_id=str(application_id),
                job_url=job_url,
                mode=mode,
            ))
            await event_bus.emit(SessionValidated(
                application_id=str(application_id),
                portal_name=str(portal_name),
                is_valid=bool(session_payload) or portal_name == "unknown",
            ))
            result = await self.browser_core.fill_application_form(
                url=job_url,
                profile_data=profile_data,
                resume_path=resume_path,
                mode=mode,
                browser_context=browser_context,
                user_data_dir=browser_context.get("user_data_dir") if browser_context else None,
            )

            logger.info(
                "task_execution_completed",
                extra={
                    "application_id": application_id,
                    "status": result.get("status"),
                    "ats_type": result.get("ats_type"),
                    "submitted": result.get("submitted", False)
                }
            )

            await event_bus.emit(ApplicationSubmitted(
                application_id=str(application_id),
                ats_type=result.get("ats_type", "unknown"),
                submitted=result.get("submitted", False),
            ))

            browser_requires_review = bool(
                result.get("requires_manual_review")
                or result.get("status") == "review_required"
                or result.get("portal_name") in {"linkedin", "naukri", "glassdoor"}
            )
            status = (
                "Submitted"
                if result.get("submitted")
                else ("Scheduled" if (requires_review or browser_requires_review) else "Auto-Filled")
            )
            await event_bus.emit(StatusSaved(
                application_id=str(application_id),
                status=status,
            ))
            await self._save_application_status(
                application_id,
                status,
                result.get("error") or "Browser application flow completed.",
            )

        except Exception as e:
            logger.error(
                "task_execution_failed",
                extra={
                    "application_id": application_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            await event_bus.emit(StatusSaved(
                application_id=str(application_id),
                status="Failed",
            ))
            await self._save_application_status(application_id, "Failed", str(e))

    async def _save_application_status(
        self,
        application_id: str | None,
        status: str,
        notes: str,
    ) -> None:
        """Persist worker progress so the UI reflects the real browser outcome."""
        if not application_id:
            return

        try:
            from datetime import datetime
            from sqlalchemy import select

            async with SessionLocal() as session:
                result = await session.execute(
                    select(Application).where(Application.id == application_id)
                )
                application = result.scalar_one_or_none()
                if application is None:
                    logger.warning("application_record_missing", extra={"application_id": application_id})
                    return

                application.status = status
                application.notes = notes[:1000]
                if status == "Submitted":
                    application.date_applied = datetime.utcnow()
                await session.commit()
        except Exception:
            logger.exception(
                "application_status_persistence_failed",
                extra={"application_id": application_id, "status": status},
            )

    async def _handle_shutdown(self, sig: signal.Signals) -> None:
        """Handle shutdown signals gracefully."""
        logger.info(
            "shutdown_signal_received",
            extra={"signal": sig.name}
        )
        self.running = False
        self._shutdown_event.set()

    async def shutdown(self) -> None:
        """Gracefully shutdown the worker."""
        logger.info("worker_shutting_down")
        self.running = False
        await self.queue.close()
        logger.info("worker_shutdown_complete")


async def main() -> None:
    """Main entry point for the browser worker daemon."""
    worker = BrowserWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("keyboard_interrupt_received")
    except Exception as e:
        logger.exception(
            "worker_fatal_error",
            extra={"error": str(e), "error_type": type(e).__name__}
        )
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
