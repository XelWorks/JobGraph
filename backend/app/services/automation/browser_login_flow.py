import json
from typing import Any


class PortalLoginFlow:
    """Helpers for the browser-based portal login flow used before saving an encrypted session."""

    LOGIN_URLS = {
        "linkedin": "https://www.linkedin.com/login",
        "naukri": "https://login.naukri.com/nLogin/Login.php",
        "glassdoor": "https://www.glassdoor.com/profile/login_input.htm",
        "greenhouse": "https://boards.greenhouse.io/signin",
        "lever": "https://www.lever.co/",
        "workday": "https://www.myworkday.com/",
        "indeed": "https://secure.indeed.com/account/login",
    }

    @staticmethod
    def portal_login_url(portal_name: str) -> str:
        normalized = (portal_name or "").strip().lower()
        return PortalLoginFlow.LOGIN_URLS.get(normalized, "https://www.google.com")

    @staticmethod
    def build_session_payload(cookies: list[dict[str, Any]] | None, portal_name: str | None = None) -> str:
        payload = {
            "portal": (portal_name or "unknown").strip(),
            "login_flow": "browser_session",
            "cookies": cookies or [],
            "captured_at": "browser_popup_login",
        }
        return json.dumps(payload)
