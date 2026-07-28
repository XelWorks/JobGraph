import logging
import uuid

from app.domain.profile import Skill, UserProfile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class ProfileRepository:
    async def get_by_user_id(self, db: AsyncSession, user_id: uuid.UUID) -> UserProfile | None:
        """Retrieve the user profile by user_id."""
        query = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def save_profile(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        phone: str | None,
        preferred_roles: list[str] | None,
        preferred_locations: list[str] | None,
        target_salary: int | None,
        skills: list[str]
    ) -> UserProfile:
        """Create or update a user profile along with their skills list."""
        if target_salary is not None and target_salary < 0:
            raise ValueError("Target salary cannot be negative.")
        if not skills:
            raise ValueError("Skills list cannot be empty.")

        profile = await self.get_by_user_id(db, user_id)
        if not profile:
            profile = UserProfile(
                user_id=user_id,
                phone=phone,
                preferred_roles=preferred_roles,
                preferred_locations=preferred_locations,
                target_salary=target_salary,
            )
            db.add(profile)
            await db.flush()  # Populates profile.id
        else:
            profile.phone = phone
            profile.preferred_roles = preferred_roles
            profile.preferred_locations = preferred_locations
            profile.target_salary = target_salary

        # Clear existing skills and insert new ones to avoid duplicates
        existing_skills_query = select(Skill).where(Skill.profile_id == profile.id)
        existing_skills_result = await db.execute(existing_skills_query)
        for old_skill in existing_skills_result.scalars():
            await db.delete(old_skill)

        for skill_name in skills:
            new_skill = Skill(profile_id=profile.id, name=skill_name.strip())
            db.add(new_skill)

        await db.commit()
        # Re-fetch profile to load selectin relationships
        query = select(UserProfile).where(UserProfile.id == profile.id)
        refetched = await db.execute(query)
        return refetched.scalar_one()

    async def update_resume_key(self, db: AsyncSession, user_id: uuid.UUID, resume_key: str) -> UserProfile:
        """Update the master resume storage key for a user's profile."""
        profile = await self.get_by_user_id(db, user_id)
        if not profile:
            profile = UserProfile(
                user_id=user_id,
                master_resume_key=resume_key
            )
            db.add(profile)
        else:
            profile.master_resume_key = resume_key

        await db.commit()
        query = select(UserProfile).where(UserProfile.id == profile.id)
        refetched = await db.execute(query)
        return refetched.scalar_one()

profile_repository = ProfileRepository()
