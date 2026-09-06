import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class ChromeSessionManager:
    """Persistent Chrome session manager for user-controlled browser automation."""

    def __init__(self, portal_name: str, user_data_dir: str, session_payload: str | None = None) -> None:
        self.portal_name = (portal_name or "").strip().lower()
        self.user_data_dir = user_data_dir
        self.session_payload = session_payload

    def build_context(self) -> dict[str, Any]:
        return {
            "portal": self.portal_name,
            "browser": "chrome",
            "user_data_dir": self.user_data_dir,
            "session_present": bool(self.session_payload),
            "manual_review_required": self.portal_name in {"linkedin", "naukri", "glassdoor"},
            "mode": "persistent_chrome_profile",
        }


class PortalAutomationRuntime:
    """Safe browser automation runtime for user-controlled Chrome workflows.

    This layer is designed around the real requirement: a human-like Chrome-based
    browser session that opens job portals, uses saved account state, and pauses for
    review when the site triggers anti-bot or verification steps.
    """

    SUPPORTED_PORTALS = {"greenhouse", "lever", "linkedin", "naukri", "glassdoor", "unknown"}
    SAFE_REVIEW_PORTALS = {"linkedin", "naukri", "glassdoor"}

    def __init__(self, portal_name: str, session_payload: str | None = None) -> None:
        portal_value = (portal_name or "").strip().lower()
        self.portal_name = portal_value or "unknown"
        self.session_payload = session_payload

    def validate_portal(self) -> bool:
        if self.portal_name in {"", "unknown"}:
            return True
        if self.portal_name not in self.SUPPORTED_PORTALS:
            logger.warning("unsupported_portal_disallowed", extra={"portal": self.portal_name})
            return False
        return True

    def needs_manual_review(self) -> bool:
        return self.portal_name in self.SAFE_REVIEW_PORTALS

    def _session_summary(self) -> dict[str, Any]:
        if not self.session_payload:
            return {"cookie_count": 0, "keys": [], "has_session": False}

        try:
            import json
            payload = json.loads(self.session_payload)
        except (TypeError, ValueError):
            return {"cookie_count": 0, "keys": [], "has_session": False, "raw_present": bool(self.session_payload)}

        if isinstance(payload, dict):
            cookies = payload.get("cookies") or payload.get("cookie")
            if isinstance(cookies, list):
                return {
                    "cookie_count": len(cookies),
                    "keys": [str(item.get("name")) for item in cookies if isinstance(item, dict) and item.get("name")],
                    "has_session": True,
                }
            if isinstance(cookies, dict):
                return {
                    "cookie_count": len(cookies),
                    "keys": list(cookies.keys()),
                    "has_session": True,
                }
            return {"cookie_count": 0, "keys": list(payload.keys()), "has_session": True}

        if isinstance(payload, list):
            return {"cookie_count": len(payload), "keys": [str(item) for item in payload], "has_session": True}

        return {"cookie_count": 0, "keys": [], "has_session": bool(payload)}

    def resolve_user_data_dir(self, user_data_dir: str | None = None) -> str:
        """Resolve a valid Chrome profile directory for the active OS and user environment."""
        if user_data_dir and user_data_dir.strip():
            return user_data_dir.strip()

        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return os.path.join(local_app_data, "Google", "Chrome", "User Data")

        home_dir = os.path.expanduser("~")
        for candidate in [
            os.path.join(home_dir, "AppData", "Local", "Google", "Chrome", "User Data"),
            os.path.join(home_dir, ".config", "google-chrome", "Default"),
            os.path.join("C:", "Users", "default", "AppData", "Local", "Google", "Chrome", "User Data"),
        ]:
            if os.path.exists(candidate):
                return candidate

        return os.path.join("C:/", "Users", "default", "AppData", "Local", "Google", "Chrome", "User Data")

    def build_browser_context(self, user_data_dir: str | None = None) -> dict[str, Any]:
        if not self.validate_portal():
            raise ValueError(f"Portal '{self.portal_name}' is not supported by the safe browser runtime.")

        session_summary = self._session_summary()
        normalized_dir = self.resolve_user_data_dir(user_data_dir)

        return {
            "portal": self.portal_name,
            "browser": "chrome",
            "browser_profile": "persistent",
            "user_data_dir": normalized_dir,
            "session_present": bool(self.session_payload),
            "session_summary": session_summary,
            "mode": "human_like_browser",
            "manual_review_required": self.needs_manual_review(),
        }

    def should_pause_for_review(self, page_status: str | None = None) -> bool:
        if page_status is None:
            return self.needs_manual_review()
        return page_status.lower() in {"captcha", "mfa", "verification", "challenge", "suspicious"}

    def build_execution_plan(
        self,
        application_id: str,
        job_url: str,
        user_data_dir: str | None = None,
    ) -> dict[str, Any]:
        browser_context = self.build_browser_context(user_data_dir=user_data_dir)
        actions = [
            "navigate_to_job",
            "confirm_logged_in_session",
            "fill_application_fields",
            "upload_resume",
            "answer_dynamic_questions",
            "submit_application",
        ]
        if self.needs_manual_review():
            actions.insert(4, "pause_for_review")

        return {
            "application_id": application_id,
            "job_url": job_url,
            "portal": self.portal_name,
            "launch_mode": "persistent_profile" if user_data_dir else "new_context",
            "review_required": self.needs_manual_review(),
            "browser": browser_context,
            "actions": actions,
            "tracking": {
                "status": "Tracked",
                "browser": "chrome",
                "requires_review": self.needs_manual_review(),
            },
        }

    def create_application_tracking(self, application_id: str, job_url: str) -> dict[str, Any]:
        return {
            "application_id": application_id,
            "job_url": job_url,
            "portal": self.portal_name,
            "status": "Tracked",
            "browser": "chrome",
            "requires_review": self.needs_manual_review(),
        }
