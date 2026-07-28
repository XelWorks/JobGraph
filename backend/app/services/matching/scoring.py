import logging
import re

from app.domain.job import JobPosting, MatchScore
from app.domain.profile import UserProfile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("app.services.matching.scoring")

class JobMatchingService:
    def calculate_skill_score(self, profile_skills: list[str], job_description: str | None, job_title: str) -> int:
        """
        Evaluate Skill Match (40% weight).
        Performs simple keyword scanning in description and title.
        Returns a score from 0 to 100.
        """
        if not profile_skills:
            return 0

        text_to_scan = f"{job_title} {job_description or ''}".lower()
        matched_count = 0

        for skill in profile_skills:
            # Word boundary regex check for skill keywords - with a fallback for partial matches on common symbols
            skill_lower = skill.lower()
            pattern = rf"\b{re.escape(skill_lower)}\b"
            if re.search(pattern, text_to_scan):
                matched_count += 1
            elif skill_lower in ["postgresql", "postgres"] and ("postgres" in text_to_scan or "postgresql" in text_to_scan):
                # Spec-echo fallback for postgresql/postgres aliases
                matched_count += 1

        # Simple ratio of matched skills to total configured skills
        ratio = matched_count / len(profile_skills)
        return min(100, int(ratio * 100))

    def calculate_experience_score(self, profile_preferred_roles: list[str] | None, job_title: str) -> int:
        """
        Evaluate Experience/Role Match (30% weight).
        Matches job title against preferred roles.
        Returns a score from 0 to 100.
        """
        if not profile_preferred_roles:
            return 100  # Default to neutral/full if no preferences specified

        job_title_lower = job_title.lower()

        for role in profile_preferred_roles:
            role_lower = role.lower()
            # If the job title contains the preferred role or vice versa
            if role_lower in job_title_lower or job_title_lower in role_lower:
                return 100

        # Partial match checklist
        for role in profile_preferred_roles:
            words = [w for w in role.lower().split() if len(w) > 3]
            for w in words:
                if w in job_title_lower:
                    return 60  # Partial match

        return 0

    def calculate_location_score(self, profile_preferred_locations: list[str] | None, job_location: str | None) -> int:
        """
        Evaluate Location Match (15% weight).
        Checks match between candidate preferences and job posting location.
        Returns a score from 0 to 100.
        """
        if not profile_preferred_locations:
            return 100  # Neutral full score if candidate doesn't restrict location

        if not job_location:
            return 50  # Missing location is neutral partial

        job_loc_lower = job_location.lower()

        for loc in profile_preferred_locations:
            loc_lower = loc.lower()
            if loc_lower in job_loc_lower or job_loc_lower in loc_lower:
                return 100

        # Flexible Remote match
        is_remote_pref = any("remote" in loc.lower() for loc in profile_preferred_locations)
        is_remote_job = "remote" in job_loc_lower or "anywhere" in job_loc_lower or "telecommute" in job_loc_lower

        if is_remote_pref and is_remote_job:
            return 100

        return 0

    def calculate_salary_score(self, profile_target_salary: int | None, job_description: str | None) -> int:
        """
        Evaluate Salary Match (15% weight).
        If job description lists salary ranges, parse and compare against targets.
        If no salary lists can be extracted, return a neutral base score of 80.
        Returns a score from 0 to 100.
        """
        if not profile_target_salary or profile_target_salary <= 0:
            return 100

        if not job_description:
            return 80  # Neutral baseline

        # Regex scanning for common salary markers e.g. $120,000, $140k, 150,000
        salary_markers = re.findall(r"\$(\d{1,3}(?:,\d{3})+|\d+k|\d+)", job_description.lower())

        if not salary_markers:
            return 80  # Neutral baseline

        parsed_salaries = []
        for marker in salary_markers:
            try:
                # Remove commas
                cleaned = marker.replace(",", "")
                if "k" in cleaned:
                    val = int(cleaned.replace("k", "")) * 1000
                else:
                    val = int(cleaned)
                # Keep values in realistic salary range boundaries
                if 30000 <= val <= 500000:
                    parsed_salaries.append(val)
            except ValueError:
                continue

        if not parsed_salaries:
            return 80  # Neutral baseline

        max_job_salary = max(parsed_salaries)

        # If job's max found salary exceeds or matches candidate target salary
        if max_job_salary >= profile_target_salary:
            return 100

        # Calculate percentage gap match score
        pct = max_job_salary / profile_target_salary
        return max(0, int(pct * 100))

    async def score_and_evaluate_job(
        self,
        db: AsyncSession,
        profile: UserProfile,
        job_posting: JobPosting,
        threshold: int = 70
    ) -> MatchScore:
        """
        Score a single discovered job posting against a candidate's profile.
        Weights: Skill (40%), Experience (30%), Location (15%), Salary (15%).
        Auto-archives the posting if overall score falls below the threshold.
        """
        profile_skills = [s.name for s in profile.skills]

        skill_score = self.calculate_skill_score(profile_skills, job_posting.description_text, job_posting.title)
        experience_score = self.calculate_experience_score(profile.preferred_roles, job_posting.title)
        location_score = self.calculate_location_score(profile.preferred_locations, job_posting.location)
        salary_score = self.calculate_salary_score(profile.target_salary, job_posting.description_text)

        # Calculate overall weighted score
        overall_score = int(
            (skill_score * 0.40) +
            (experience_score * 0.30) +
            (location_score * 0.15) +
            (salary_score * 0.15)
        )

        # Enforce boundary constraint
        overall_score = max(0, min(100, overall_score))
        is_archived = overall_score < threshold

        # Deduplicate: Check if a MatchScore already exists for this job posting
        query = select(MatchScore).where(MatchScore.job_posting_id == job_posting.id)
        existing = await db.execute(query)
        match_record = existing.scalar_one_or_none()

        if not match_record:
            match_record = MatchScore(
                job_posting_id=job_posting.id,
                overall_score=overall_score,
                skill_score=skill_score,
                experience_score=experience_score,
                location_score=location_score,
                salary_score=salary_score,
                is_archived=is_archived
            )
            db.add(match_record)
        else:
            match_record.overall_score = overall_score
            match_record.skill_score = skill_score
            match_record.experience_score = experience_score
            match_record.location_score = location_score
            match_record.salary_score = salary_score
            match_record.is_archived = is_archived

        await db.commit()
        return match_record

job_matching_service = JobMatchingService()
