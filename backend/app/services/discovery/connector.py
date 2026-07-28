import abc
import logging
from typing import Any

import httpx
from app.domain.job import JobPosting
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("app.services.discovery.connector")

class BaseConnector(abc.ABC):
    """Abstract base class establishing generic interfaces for ATS integrations."""

    @property
    @abc.abstractmethod
    def platform_name(self) -> str:
        """Return the name of the ATS platform (e.g. 'Greenhouse' or 'Lever')."""
        pass

    @abc.abstractmethod
    async def fetch_jobs(self, board_token: str) -> list[dict[str, Any]]:
        """Fetch raw listings from the targeted ATS board."""
        pass

    @abc.abstractmethod
    def parse_job(self, raw_job: dict[str, Any], board_token: str) -> dict[str, Any]:
        """Normalize raw board listings into a standardized contract payload."""
        pass

    async def sync_board(self, db: AsyncSession, board_token: str) -> list[JobPosting]:
        """Perform ingestion, normalization, and deduplication of job postings."""
        logger.info(f"sync_started: platform={self.platform_name}, board={board_token}")
        synced_records = []

        try:
            raw_jobs = await self.fetch_jobs(board_token)
        except Exception as e:
            logger.error(f"sync_fetch_failed: platform={self.platform_name}, board={board_token}, error={e}")
            return []

        for raw in raw_jobs:
            try:
                parsed = self.parse_job(raw, board_token)

                # Check for existing listing in DB to ensure deduplication
                query = select(JobPosting).where(
                    JobPosting.platform == self.platform_name,
                    JobPosting.external_job_id == str(parsed["external_job_id"]),
                    JobPosting.board_token == board_token
                )
                existing = await db.execute(query)
                record = existing.scalar_one_or_none()

                if not record:
                    record = JobPosting(
                        platform=self.platform_name,
                        external_job_id=str(parsed["external_job_id"]),
                        board_token=board_token,
                        title=parsed["title"],
                        company=parsed["company"],
                        location=parsed.get("location"),
                        url=parsed["url"],
                        description_text=parsed.get("description_text"),
                        raw_json=raw
                    )
                    db.add(record)
                    synced_records.append(record)
                else:
                    # Update fields in case job postings changed dynamically
                    record.title = parsed["title"]
                    record.company = parsed["company"]
                    record.location = parsed.get("location")
                    record.url = parsed["url"]
                    record.description_text = parsed.get("description_text")
                    record.raw_json = raw
                    synced_records.append(record)

            except Exception as e:
                logger.error(f"sync_parsing_failed: platform={self.platform_name}, job_id={raw.get('id')}, error={e}")
                continue

        await db.commit()
        logger.info(f"sync_completed: platform={self.platform_name}, board={board_token}, total_synced={len(synced_records)}")
        return synced_records


class GreenhouseConnector(BaseConnector):
    """Greenhouse Job Board Integration Connector."""

    @property
    def platform_name(self) -> str:
        return "Greenhouse"

    async def fetch_jobs(self, board_token: str) -> list[dict[str, Any]]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=15.0)
            if response.status_code != 200:
                logger.warning(f"greenhouse_api_error: board={board_token}, status={response.status_code}")
                return []
            data = response.json()
            return data.get("jobs", [])

    def parse_job(self, raw_job: dict[str, Any], board_token: str) -> dict[str, Any]:
        """Normalize Greenhouse job representation."""
        # Greenhouse listings have unique integer identifiers
        external_id = raw_job.get("id")
        if external_id is None:
            raise ValueError("Greenhouse listing is missing unique 'id'.")

        title = raw_job.get("title")
        if not title:
            raise ValueError("Greenhouse listing is missing 'title'.")

        # Standard corporate Greenhouse listing url pattern
        job_url = raw_job.get("absolute_url") or f"https://boards.greenhouse.io/{board_token}/jobs/{external_id}"

        # Location mapping from Greenhouse location object
        location = "Remote"
        loc_obj = raw_job.get("location")
        if isinstance(loc_obj, dict):
            location = loc_obj.get("name") or "Remote"
        elif isinstance(loc_obj, str):
            location = loc_obj

        return {
            "external_job_id": str(external_id),
            "title": title.strip(),
            "company": board_token.title(),  # Token usually matches corporate namespace
            "location": location,
            "url": job_url,
            "description_text": raw_job.get("content") or ""
        }


class LeverConnector(BaseConnector):
    """Lever Job Board Integration Connector."""

    @property
    def platform_name(self) -> str:
        return "Lever"

    async def fetch_jobs(self, board_token: str) -> list[dict[str, Any]]:
        url = f"https://api.lever.co/v0/postings/{board_token}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=15.0)
            if response.status_code != 200:
                logger.warning(f"lever_api_error: board={board_token}, status={response.status_code}")
                return []
            return response.json()

    def parse_job(self, raw_job: dict[str, Any], board_token: str) -> dict[str, Any]:
        """Normalize Lever job representation."""
        # Lever listings use UUID-style strings as IDs
        external_id = raw_job.get("id")
        if not external_id:
            raise ValueError("Lever listing is missing unique 'id'.")

        title = raw_job.get("text")
        if not title:
            raise ValueError("Lever listing is missing 'text' (title).")

        job_url = raw_job.get("hostedUrl") or f"https://jobs.lever.co/{board_token}/{external_id}"

        # Lever locations mapped from categorized location object
        location = "Remote"
        categories = raw_job.get("categories")
        if isinstance(categories, dict):
            location = categories.get("location") or "Remote"

        # Compile plain text description from Lever subsections
        description_parts = []
        desc_raw = raw_job.get("descriptionPlain")
        if desc_raw:
            description_parts.append(desc_raw)

        lists = raw_job.get("lists")
        if isinstance(lists, list):
            for section in lists:
                if isinstance(section, dict):
                    title_sec = section.get("text")
                    content_sec = section.get("content")
                    if title_sec:
                        description_parts.append(f"\n{title_sec}:")
                    if isinstance(content_sec, list):
                        description_parts.extend([f"- {bullet}" for bullet in content_sec])

        description_text = "\n".join(description_parts) if description_parts else (raw_job.get("description") or "")

        return {
            "external_job_id": str(external_id),
            "title": title.strip(),
            "company": board_token.title(),
            "location": location,
            "url": job_url,
            "description_text": description_text
        }
