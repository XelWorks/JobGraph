import json

from app.services.automation.browser_login_flow import PortalLoginFlow


def test_build_cookie_payload_formats_browser_cookies():
    cookies = [
        {"name": "li_at", "value": "abc123"},
        {"name": "JSESSIONID", "value": "xyz789"},
    ]

    payload = PortalLoginFlow.build_session_payload(cookies)
    data = json.loads(payload)

    assert data["cookies"][0]["name"] == "li_at"
    assert data["cookies"][1]["value"] == "xyz789"
    assert data["login_flow"] == "browser_session"


def test_login_url_map_for_linkedin():
    url = PortalLoginFlow.portal_login_url("LinkedIn")
    assert "linkedin.com/login" in url
