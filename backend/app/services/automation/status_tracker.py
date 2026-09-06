import logging
from datetime import datetime
from uuid import UUID

from app.infrastructure.db.application_repository import application_repository
from app.infrastructure.db.session import SessionLocal
from app.services.automation.events import ApplicationSubmitted, StatusSaved

logger = logging.getLogger(__name__)


async def persist_status_saved_event(event: StatusSaved) -> None:
    """Persist a worker status update into the application record."""
    try:
        application_id = UUID(str(event.application_id))
    except (TypeError, ValueError):
        logger.warning("invalid_application_id_for_status_save", extra={"application_id": event.application_id})
        return

    async with SessionLocal() as session:
        try:
            await application_repository.update_artifacts(
                session,
                application_id,
                status=event.status,
                date_applied=datetime.utcnow() if event.status == "Submitted" else None,
            )
        except Exception as exc:
            logger.error(
                "status_persistence_failed",
                extra={
                    "application_id": str(application_id),
                    "status": event.status,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
            )
            raise


async def persist_application_submitted_event(event: ApplicationSubmitted) -> None:
    """Persist ATS-type and submission metadata for the application tracking record."""
    try:
        application_id = UUID(str(event.application_id))
    except (TypeError, ValueError):
        logger.warning("invalid_application_id_for_submit_event", extra={"application_id": event.application_id})
        return

    async with SessionLocal() as session:
        try:
            await application_repository.update_artifacts(
                session,
                application_id,
                notes=f"ATS={event.ats_type}; submitted={str(event.submitted).lower()}",
                status="Submitted" if event.submitted else "Auto-Filled",
                date_applied=datetime.utcnow() if event.submitted else None,
            )
        except Exception as exc:
            logger.error(
                "submission_metadata_persistence_failed",
                extra={
                    "application_id": str(application_id),
                    "ats_type": event.ats_type,
                    "submitted": event.submitted,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
            )
            raise
