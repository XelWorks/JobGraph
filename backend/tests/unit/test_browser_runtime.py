from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from app.infrastructure.browser.playwright_client import PlaywrightBrowserCore
from app.services.automation.browser_runtime import ChromeSessionManager, PortalAutomationRuntime


def test_chrome_session_manager_builds_review_ready_context() -> None:
    manager = ChromeSessionManager(
        portal_name="linkedin",
        user_data_dir="C:/Users/test/AppData/Local/Google/Chrome/User Data",
        session_payload='{"cookies": "demo"}',
    )

    context = manager.build_context()

    assert context["browser"] == "chrome"
    assert context["portal"] == "linkedin"
    assert context["manual_review_required"] is True
    assert context["user_data_dir"].endswith("User Data")
    assert context["session_present"] is True


def test_runtime_tracks_application_with_manual_review_required() -> None:
    runtime = PortalAutomationRuntime("linkedin", session_payload='{"cookies": "demo"}')

    tracking = runtime.create_application_tracking(
        application_id="app-42",
        job_url="https://www.linkedin.com/jobs/view/123456789",
    )

    assert tracking["application_id"] == "app-42"
    assert tracking["portal"] == "linkedin"
    assert tracking["status"] == "Tracked"
    assert tracking["requires_review"] is True


def test_runtime_builds_persistent_chrome_session_context() -> None:
    runtime = PortalAutomationRuntime(
        "linkedin",
        session_payload='{"cookies": [{"name": "li_at", "value": "abc123"}]}'
    )

    context = runtime.build_browser_context(user_data_dir="C:/Users/test/AppData/Local/Google/Chrome/User Data")

    assert context["browser"] == "chrome"
    assert context["portal"] == "linkedin"
    assert context["user_data_dir"].endswith("User Data")
    assert context["session_present"] is True
    assert context["browser_profile"] == "persistent"
    assert context["session_summary"]["cookie_count"] == 1


def test_runtime_builds_execution_plan_for_review_required_portal() -> None:
    runtime = PortalAutomationRuntime(
        "linkedin",
        session_payload='{"cookies": [{"name": "li_at", "value": "abc123"}]}'
    )

    plan = runtime.build_execution_plan(
        application_id="app-77",
        job_url="https://www.linkedin.com/jobs/view/123456789",
        user_data_dir="C:/Users/test/AppData/Local/Google/Chrome/User Data",
    )

    assert plan["application_id"] == "app-77"
    assert plan["portal"] == "linkedin"
    assert plan["launch_mode"] == "persistent_profile"
    assert plan["review_required"] is True
    assert plan["browser"]["browser"] == "chrome"
    assert plan["actions"][0] == "navigate_to_job"
    assert "pause_for_review" in plan["actions"]


def test_runtime_resolves_default_chrome_profile_path() -> None:
    runtime = PortalAutomationRuntime("linkedin")

    resolved = runtime.resolve_user_data_dir(None)

    assert resolved.endswith("Google/Chrome/User Data") or resolved.endswith("Google\\Chrome\\User Data")


@pytest.mark.asyncio
async def test_portal_action_handler_routes_to_linkedin_flow() -> None:
    core = PlaywrightBrowserCore()

    class FakeLocator:
        async def count(self) -> int:
            return 1

        async def is_visible(self) -> bool:
            return True

        async def click(self) -> None:
            return None

    class FakePage:
        def locator(self, selector: str):
            return FakeLocator()

    result: dict[str, object] = {}
    handled = await core._handle_portal_specific_actions(
        page=FakePage(),
        portal_name="linkedin",
        profile_data={"first_name": "Jane", "last_name": "Doe"},
        resume_path="/tmp/resume.pdf",
        result=result,
    )

    assert handled is True
    assert result["portal_flow"] == "linkedin"


@pytest.mark.asyncio
async def test_portal_action_handler_requires_review_when_apply_cta_missing() -> None:
    core = PlaywrightBrowserCore()

    class MissingApplyLocator:
        async def count(self) -> int:
            return 0

        async def click(self) -> None:
            raise AssertionError("Apply button should not be clicked when absent")

    class FakePage:
        def locator(self, selector: str):
            return MissingApplyLocator()

    result: dict[str, object] = {}
    handled = await core._handle_portal_specific_actions(
        page=FakePage(),
        portal_name="linkedin",
        profile_data={"first_name": "Jane", "last_name": "Doe"},
        resume_path="/tmp/resume.pdf",
        result=result,
    )

    assert handled is True
    assert result["status"] == "review_required"
    assert result["requires_manual_review"] is True


@pytest.mark.asyncio
async def test_preflight_portal_gate_detects_sign_in_state() -> None:
    core = PlaywrightBrowserCore()

    class SignInLocator:
        async def count(self) -> int:
            return 1

    class FakePage:
        def locator(self, selector: str):
            return SignInLocator()

    should_pause = await core._preflight_portal_gate(
        page=FakePage(),
        portal_name="linkedin",
        browser_context={"manual_review_required": False},
    )

    assert should_pause is True


@pytest.mark.asyncio
async def test_page_state_evaluation_declares_manual_review_for_sign_in_gate() -> None:
    core = PlaywrightBrowserCore()

    class SignInLocator:
        def __init__(self, matches: bool = False) -> None:
            self.matches = matches

        async def count(self) -> int:
            return 1 if self.matches else 0

    class FakePage:
        def locator(self, selector: str):
            matches = selector in {"text=Sign in", "text=Log in", "text=Join now"}
            return SignInLocator(matches=matches)

    state = await core._evaluate_page_state(
        page=FakePage(),
        portal_name="linkedin",
        browser_context={"manual_review_required": False},
    )

    assert state["login_required"] is True
    assert state["verification_required"] is False
    assert state["requires_manual_review"] is True


@pytest.mark.asyncio
async def test_fill_application_form_stops_for_manual_review_page_state() -> None:
    core = PlaywrightBrowserCore(headless=True)
    resume_file = Path("/tmp") / "resume_for_review_test.pdf"
    resume_file.parent.mkdir(parents=True, exist_ok=True)
    resume_file.write_bytes(b"mock resume")

    class FakePage:
        def __init__(self) -> None:
            self._redirected = False

        def set_default_timeout(self, _timeout: int) -> None:
            return None

        async def goto(self, url: str, wait_until: str = "domcontentloaded") -> None:
            self._redirected = True

    class FakeContext:
        def __init__(self) -> None:
            self.page = FakePage()

        async def new_page(self):
            return self.page

        async def close(self) -> None:
            return None

    class FakeBrowser:
        def __init__(self) -> None:
            self.context = FakeContext()

        async def new_context(self, **kwargs):
            return self.context

        async def close(self) -> None:
            return None

    class FakePlaywright:
        class chromium:
            @staticmethod
            async def launch(**kwargs):
                return FakeBrowser()

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.infrastructure.browser.playwright_client.async_playwright", lambda: FakePlaywright())
        mp.setattr(
            core,
            "_evaluate_page_state",
            AsyncMock(return_value={"login_required": True, "verification_required": False, "requires_manual_review": True}),
        )
        result = await core.fill_application_form(
            url="https://www.linkedin.com/jobs/view/123",
            profile_data={"first_name": "Jane", "last_name": "Doe", "email": "jane@example.com"},
            resume_path=str(resume_file),
            mode="Autonomous",
            browser_context={"portal": "linkedin"},
        )

    assert result["status"] == "review_required"
    assert result["requires_manual_review"] is True
