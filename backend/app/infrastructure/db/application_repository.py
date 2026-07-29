import logging
import uuid

from app.domain.job import Application
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class ApplicationRepository:
    async def get_by_id(self, db: AsyncSession, app_id: uuid.UUID) -> Application | None:
        """Retrieve an application by id."""
        query = select(Application).where(Application.id == app_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user_and_job(self, db: AsyncSession, user_id: uuid.UUID, job_posting_id: uuid.UUID) -> Application | None:
        """Retrieve an application by user_id and job_posting_id."""
        query = select(Application).where(
            Application.user_id == user_id,
            Application.job_posting_id == job_posting_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_application(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        job_posting_id: uuid.UUID,
        mode: str = "Manual",
        status: str = "Backlog",
        notes: str | None = None
    ) -> Application:
        """Create a new application record."""
        application = Application(
            user_id=user_id,
            job_posting_id=job_posting_id,
            mode=mode,
            status=status,
            notes=notes
        )
        db.add(application)
        await db.commit()
        # Re-fetch to load lazy/selectin relationships
        query = select(Application).where(Application.id == application.id)
        refetched = await db.execute(query)
        return refetched.scalar_one()

    async def update_artifacts(
        self,
        db: AsyncSession,
        app_id: uuid.UUID,
        resume_key: str | None = None,
        cover_letter_key: str | None = None,
        status: str | None = None,
        resume_data: dict | None = None,
        cover_letter_data: dict | None = None
    ) -> Application:
        """Update the resume key, cover letter key, status, or raw tailored data of an application."""
        application = await self.get_by_id(db, app_id)
        if not application:
            raise ValueError(f"Application with ID {app_id} does not exist.")

        if resume_key is not None:
            application.tailored_resume_key = resume_key
        if cover_letter_key is not None:
            application.cover_letter_key = cover_letter_key
        if status is not None:
            application.status = status
        if resume_data is not None:
            application.tailored_resume_data = resume_data
        if cover_letter_data is not None:
            application.tailored_cover_letter_data = cover_letter_data

        await db.commit()
        query = select(Application).where(Application.id == application.id)
        refetched = await db.execute(query)
        return refetched.scalar_one()

application_repository = ApplicationRepository()
