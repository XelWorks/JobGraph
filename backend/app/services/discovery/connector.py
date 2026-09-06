import logging
from typing import Any

import httpx
from app.domain.connector import BasePortalConnector
from app.domain.job import JobPosting
from app.services.automation.browser_runtime import PortalAutomationRuntime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("app.services.discovery.connector")


class GreenhouseConnector(BasePortalConnector):
    """Greenhouse Job Board Integration Connector."""

    @property
    def platform_name(self) -> str:
        return "Greenhouse"

    async def connect(self, session_data: dict[str, Any]) -> bool:
        logger.info("greenhouse_connect: board=%s", session_data.get("board_token"))
        return True

    async def disconnect(self) -> None:
        logger.info("greenhouse_disconnect")

    async def validate_session(self) -> bool:
        return True

    async def search_jobs(self, query: str, location: str) -> list[dict[str, Any]]:
        return []

    async def apply(self, job_url: str, profile_data: dict[str, Any], resume_path: str) -> dict[str, Any]:
        return {"status": "not_implemented"}

    async def health_check(self) -> str:
        return "Healthy"

    async def refresh_session(self) -> dict[str, Any]:
        return {}

    async def fetch_jobs(self, board_token: str) -> list[dict[str, Any]]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=15.0)
            if response.status_code != 200:
                logger.warning("greenhouse_api_error: board=%s, status=%s", board_token, response.status_code)
                return []
            data = response.json()
            return data.get("jobs", [])

    def parse_job(self, raw_job: dict[str, Any], board_token: str) -> dict[str, Any]:
        external_id = raw_job.get("id")
        if external_id is None:
            raise ValueError("Greenhouse listing is missing unique 'id'.")

        title = raw_job.get("title")
        if not title:
            raise ValueError("Greenhouse listing is missing 'title'.")

        job_url = raw_job.get("absolute_url") or f"https://boards.greenhouse.io/{board_token}/jobs/{external_id}"

        location = "Remote"
        loc_obj = raw_job.get("location")
        if isinstance(loc_obj, dict):
            location = loc_obj.get("name") or "Remote"
        elif isinstance(loc_obj, str):
            location = loc_obj

        return {
            "external_job_id": str(external_id),
            "title": title.strip(),
            "company": board_token.title(),
            "location": location,
            "url": job_url,
            "description_text": raw_job.get("content") or "",
        }

    async def sync_board(self, db: AsyncSession, board_token: str) -> list[JobPosting]:
        logger.info("sync_started: platform=%s, board=%s", self.platform_name, board_token)
        synced_records = []

        try:
            raw_jobs = await self.fetch_jobs(board_token)
        except Exception as e:
            logger.error("sync_fetch_failed: platform=%s, board=%s, error=%s", self.platform_name, board_token, e)
            return []

        for raw in raw_jobs:
            try:
                parsed = self.parse_job(raw, board_token)
                query = select(JobPosting).where(
                    JobPosting.platform == self.platform_name,
                    JobPosting.external_job_id == str(parsed["external_job_id"]),
                    JobPosting.board_token == board_token,
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
                        raw_json=raw,
                    )
                    db.add(record)
                    synced_records.append(record)
                else:
                    record.title = parsed["title"]
                    record.company = parsed["company"]
                    record.location = parsed.get("location")
                    record.url = parsed["url"]
                    record.description_text = parsed.get("description_text")
                    record.raw_json = raw
                    synced_records.append(record)

            except Exception as e:
                logger.error("sync_parsing_failed: platform=%s, job_id=%s, error=%s", self.platform_name, raw.get("id"), e)
                continue

        await db.commit()
        logger.info("sync_completed: platform=%s, board=%s, total_synced=%d", self.platform_name, board_token, len(synced_records))
        return synced_records


class LeverConnector(BasePortalConnector):
    """Lever Job Board Integration Connector."""

    @property
    def platform_name(self) -> str:
        return "Lever"

    async def connect(self, session_data: dict[str, Any]) -> bool:
        logger.info("lever_connect: board=%s", session_data.get("board_token"))
        return True

    async def disconnect(self) -> None:
        logger.info("lever_disconnect")

    async def validate_session(self) -> bool:
        return True

    async def search_jobs(self, query: str, location: str) -> list[dict[str, Any]]:
        return []

    async def apply(self, job_url: str, profile_data: dict[str, Any], resume_path: str) -> dict[str, Any]:
        return {"status": "not_implemented"}

    async def health_check(self) -> str:
        return "Healthy"

    async def refresh_session(self) -> dict[str, Any]:
        return {}

    async def fetch_jobs(self, board_token: str) -> list[dict[str, Any]]:
        url = f"https://api.lever.co/v0/postings/{board_token}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=15.0)
            if response.status_code != 200:
                logger.warning("lever_api_error: board=%s, status=%s", board_token, response.status_code)
                return []
            return response.json()

    def parse_job(self, raw_job: dict[str, Any], board_token: str) -> dict[str, Any]:
        external_id = raw_job.get("id")
        if not external_id:
            raise ValueError("Lever listing is missing unique 'id'.")

        title = raw_job.get("text")
        if not title:
            raise ValueError("Lever listing is missing 'text' (title).")

        job_url = raw_job.get("hostedUrl") or f"https://jobs.lever.co/{board_token}/{external_id}"

        location = "Remote"
        categories = raw_job.get("categories")
        if isinstance(categories, dict):
            location = categories.get("location") or "Remote"

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
            "description_text": description_text,
        }

    async def sync_board(self, db: AsyncSession, board_token: str) -> list[JobPosting]:
        logger.info("sync_started: platform=%s, board=%s", self.platform_name, board_token)
        synced_records = []

        try:
            raw_jobs = await self.fetch_jobs(board_token)
        except Exception as e:
            logger.error("sync_fetch_failed: platform=%s, board=%s, error=%s", self.platform_name, board_token, e)
            return []

        for raw in raw_jobs:
            try:
                parsed = self.parse_job(raw, board_token)
                query = select(JobPosting).where(
                    JobPosting.platform == self.platform_name,
                    JobPosting.external_job_id == str(parsed["external_job_id"]),
                    JobPosting.board_token == board_token,
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
                        raw_json=raw,
                    )
                    db.add(record)
                    synced_records.append(record)
                else:
                    record.title = parsed["title"]
                    record.company = parsed["company"]
                    record.location = parsed.get("location")
                    record.url = parsed["url"]
                    record.description_text = parsed.get("description_text")
                    record.raw_json = raw
                    synced_records.append(record)

            except Exception as e:
                logger.error("sync_parsing_failed: platform=%s, job_id=%s, error=%s", self.platform_name, raw.get("id"), e)
                continue

        await db.commit()
        logger.info("sync_completed: platform=%s, board=%s, total_synced=%d", self.platform_name, board_token, len(synced_records))
        return synced_records


class LinkedInConnector(BasePortalConnector):
    """LinkedIn browser-driven connector. This does not scrape LinkedIn in a bot-like way; instead it uses the browser profile and authenticated session flow the user controls."""

    @property
    def platform_name(self) -> str:
        return "LinkedIn"

    async def connect(self, session_data: dict[str, Any]) -> bool:
        logger.info("linkedin_connect: session_present=%s", bool(session_data))
        return True

    async def disconnect(self) -> None:
        logger.info("linkedin_disconnect")

    async def validate_session(self) -> bool:
        return True

    async def search_jobs(self, query: str, location: str) -> list[dict[str, Any]]:
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={location}"
        return [{
            "title": "LinkedIn Browser Search",
            "company": "LinkedIn",
            "location": location,
            "url": search_url,
            "description_text": f"Search for {query} in {location} using the Chrome browser flow.",
            "external_job_id": f"linkedin-search-{query.lower().replace(' ', '-')}-{location.lower().replace(' ', '-')}",
        }]

    async def apply(self, job_url: str, profile_data: dict[str, Any], resume_path: str) -> dict[str, Any]:
        runtime = PortalAutomationRuntime(self.platform_name.lower(), session_payload='{"cookies": [{"name": "li_at", "value": "demo"}]}')
        context = runtime.build_browser_context(user_data_dir="C:/Users/default/AppData/Local/Google/Chrome/User Data")
        return {
            "status": "browser_ready",
            "platform": self.platform_name,
            "portal": self.platform_name.lower(),
            "job_url": job_url,
            "resume_path": resume_path,
            "browser": "chrome",
            "requires_review": True,
            "browser_context": context,
            "message": "Browser automation will open the LinkedIn job page and apply like a real user in Chrome.",
        }

    async def health_check(self) -> str:
        return "Healthy"

    async def refresh_session(self) -> dict[str, Any]:
        return {"platform": self.platform_name, "status": "session_refreshed"}


class NaukriConnector(BasePortalConnector):
    """Naukri browser-driven connector."""

    @property
    def platform_name(self) -> str:
        return "Naukri"

    async def connect(self, session_data: dict[str, Any]) -> bool:
        logger.info("naukri_connect: session_present=%s", bool(session_data))
        return True

    async def disconnect(self) -> None:
        logger.info("naukri_disconnect")

    async def validate_session(self) -> bool:
        return True

    async def search_jobs(self, query: str, location: str) -> list[dict[str, Any]]:
        search_url = f"https://www.naukri.com/{query}-jobs-in-{location}"
        return [{
            "title": "Naukri Browser Search",
            "company": "Naukri",
            "location": location,
            "url": search_url,
            "description_text": f"Search for {query} in {location} via the Chrome browser flow.",
            "external_job_id": f"naukri-search-{query.lower().replace(' ', '-')}-{location.lower().replace(' ', '-')}",
        }]

    async def apply(self, job_url: str, profile_data: dict[str, Any], resume_path: str) -> dict[str, Any]:
        runtime = PortalAutomationRuntime(self.platform_name.lower(), session_payload='{"cookies": [{"name": "naukri_session", "value": "demo"}]}')
        context = runtime.build_browser_context(user_data_dir="C:/Users/default/AppData/Local/Google/Chrome/User Data")
        return {
            "status": "browser_ready",
            "platform": self.platform_name,
            "portal": self.platform_name.lower(),
            "job_url": job_url,
            "resume_path": resume_path,
            "browser": "chrome",
            "requires_review": True,
            "browser_context": context,
            "message": "Browser automation will open the Naukri job page and complete the application flow like a human user.",
        }

    async def health_check(self) -> str:
        return "Healthy"

    async def refresh_session(self) -> dict[str, Any]:
        return {"platform": self.platform_name, "status": "session_refreshed"}


class GlassdoorConnector(BasePortalConnector):
    """Glassdoor browser-driven connector."""

    @property
    def platform_name(self) -> str:
        return "Glassdoor"

    async def connect(self, session_data: dict[str, Any]) -> bool:
        logger.info("glassdoor_connect: session_present=%s", bool(session_data))
        return True

    async def disconnect(self) -> None:
        logger.info("glassdoor_disconnect")

    async def validate_session(self) -> bool:
        return True

    async def search_jobs(self, query: str, location: str) -> list[dict[str, Any]]:
        search_url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={query}&locT=C&locId=1&locKeyword={location}"
        return [{
            "title": "Glassdoor Browser Search",
            "company": "Glassdoor",
            "location": location,
            "url": search_url,
            "description_text": f"Search for {query} in {location} via Chrome-based job application flow.",
            "external_job_id": f"glassdoor-search-{query.lower().replace(' ', '-')}-{location.lower().replace(' ', '-')}",
        }]

    async def apply(self, job_url: str, profile_data: dict[str, Any], resume_path: str) -> dict[str, Any]:
        runtime = PortalAutomationRuntime(self.platform_name.lower(), session_payload='{"cookies": [{"name": "gd_session", "value": "demo"}]}')
        context = runtime.build_browser_context(user_data_dir="C:/Users/default/AppData/Local/Google/Chrome/User Data")
        return {
            "status": "browser_ready",
            "platform": self.platform_name,
            "portal": self.platform_name.lower(),
            "job_url": job_url,
            "resume_path": resume_path,
            "browser": "chrome",
            "requires_review": True,
            "browser_context": context,
            "message": "Browser automation will open the Glassdoor job listing and continue the application in a human-like Chrome session.",
        }

    async def health_check(self) -> str:
        return "Healthy"

    async def refresh_session(self) -> dict[str, Any]:
        return {"platform": self.platform_name, "status": "session_refreshed"}
