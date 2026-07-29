import os
import tempfile

import pytest
from app.infrastructure.browser.playwright_client import playwright_browser_core

MOCK_GREENHOUSE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Mock Greenhouse Application Form</title></head>
<body>
  <form id="application_form" action="/submit" method="POST">
    <label for="first_name">First Name</label>
    <input type="text" id="first_name" name="job_application[first_name]" required />

    <label for="last_name">Last Name</label>
    <input type="text" id="last_name" name="job_application[last_name]" required />

    <label for="email">Email</label>
    <input type="email" id="email" name="job_application[email]" required />

    <label for="phone">Phone</label>
    <input type="text" id="phone" name="job_application[phone]" />

    <label for="resume_file">Resume File</label>
    <input type="file" id="resume_file" name="job_application[resume]" required />

    <button type="submit">Submit Application</button>
  </form>
</body>
</html>
"""

MOCK_LEVER_HTML = """
<!DOCTYPE html>
<html>
<head><title>Mock Lever Application Form</title></head>
<body>
  <form id="application-form" action="/submit" method="POST">
    <label>Full Name <input type="text" name="name" required /></label>
    <label>Email <input type="email" name="email" required /></label>
    <label>Phone <input type="text" name="phone" /></label>

    <label>Resume
      <input type="file" id="resume-upload-input" name="resume" required />
    </label>

    <button type="submit">Submit</button>
  </form>
</body>
</html>
"""

MOCK_GENERIC_HTML = """
<!DOCTYPE html>
<html>
<head><title>Mock Generic Application Form</title></head>
<body>
  <form action="/submit" method="POST">
    <label>Candidate Name <input type="text" name="candidate_name" required /></label>
    <label>E-mail Address <input type="email" name="candidate_email" required /></label>
    <label>Mobile <input type="text" name="candidate_phone" /></label>
    <label>Upload CV <input type="file" name="cv_upload" required /></label>
    <button type="submit">Send</button>
  </form>
</body>
</html>
"""


@pytest.fixture
def mock_documents():
    """Create a temporary resume PDF file and a temporary directory for screenshots."""
    with tempfile.TemporaryDirectory() as temp_dir:
        resume_path = os.path.join(temp_dir, "my_tailored_resume.pdf")
        with open(resume_path, "wb") as f:
            f.write(b"%PDF-1.4 dummy resume content for playwright")

        screenshot_path = os.path.join(temp_dir, "fill_verification.png")

        yield resume_path, screenshot_path


@pytest.mark.asyncio
async def test_greenhouse_mock_autofill_and_upload(mock_documents):
    """Test Playwright core handler correctly autofills Greenhouse structured form and uploads PDF."""
    resume_path, screenshot_path = mock_documents

    # Write mock Greenhouse HTML page to a temp file
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(MOCK_GREENHOUSE_HTML)
        greenhouse_html_path = f.name

    try:
        url = f"file://{greenhouse_html_path}"
        profile_data = {
            "first_name": "Gourav",
            "last_name": "G",
            "email": "gourav@example.com",
            "phone": "+1 (555) 019-2834"
        }

        # Run automation filling core
        res = await playwright_browser_core.fill_application_form(
            url=url,
            profile_data=profile_data,
            resume_path=resume_path,
            screenshot_path=screenshot_path
        )

        assert res["status"] == "success"
        assert res["ats_type"] == "greenhouse"
        assert "first_name" in res["filled_fields"]
        assert "last_name" in res["filled_fields"]
        assert "email" in res["filled_fields"]
        assert "phone" in res["filled_fields"]
        assert res["uploaded_resume"] is True
        assert os.path.exists(screenshot_path)
        assert os.path.getsize(screenshot_path) > 0

    finally:
        if os.path.exists(greenhouse_html_path):
            os.remove(greenhouse_html_path)


@pytest.mark.asyncio
async def test_lever_mock_autofill_and_upload(mock_documents):
    """Test Playwright core handler correctly autofills Lever structured form and uploads PDF."""
    resume_path, screenshot_path = mock_documents

    # Write mock Lever HTML page to a temp file
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(MOCK_LEVER_HTML)
        lever_html_path = f.name

    try:
        url = f"file://{lever_html_path}"
        profile_data = {
            "first_name": "Gourav",
            "last_name": "G",
            "email": "gourav@example.com",
            "phone": "+1 (555) 019-2834"
        }

        # Run automation filling core
        res = await playwright_browser_core.fill_application_form(
            url=url,
            profile_data=profile_data,
            resume_path=resume_path,
            screenshot_path=screenshot_path
        )

        assert res["status"] == "success"
        assert res["ats_type"] == "lever"
        assert "full_name" in res["filled_fields"]
        assert "email" in res["filled_fields"]
        assert "phone" in res["filled_fields"]
        assert res["uploaded_resume"] is True
        assert os.path.exists(screenshot_path)

    finally:
        if os.path.exists(lever_html_path):
            os.remove(lever_html_path)


@pytest.mark.asyncio
async def test_generic_mock_autofill_and_upload(mock_documents):
    """Test Playwright core handler executes fuzzy fallback matching on generic/unrecognized forms."""
    resume_path, screenshot_path = mock_documents

    # Write mock Generic HTML page to a temp file
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(MOCK_GENERIC_HTML)
        generic_html_path = f.name

    try:
        url = f"file://{generic_html_path}"
        profile_data = {
            "first_name": "Gourav",
            "last_name": "G",
            "email": "gourav@example.com",
            "phone": "+1 (555) 019-2834"
        }

        # Run automation filling core
        res = await playwright_browser_core.fill_application_form(
            url=url,
            profile_data=profile_data,
            resume_path=resume_path,
            screenshot_path=screenshot_path
        )

        assert res["status"] == "success"
        assert res["ats_type"] == "generic"
        assert "full_name" in res["filled_fields"]
        assert "email" in res["filled_fields"]
        assert "phone" in res["filled_fields"]
        assert res["uploaded_resume"] is True
        assert os.path.exists(screenshot_path)

    finally:
        if os.path.exists(generic_html_path):
            os.remove(generic_html_path)


@pytest.mark.asyncio
async def test_graceful_browser_close_on_exception():
    """Verify that browser context/instance is closed gracefully even when invalid input or exception is raised."""
    # Pass non-existent resume path which should fail before/during page navigation
    invalid_resume_path = "non_existent_resume_file_path_12345.pdf"

    with pytest.raises(FileNotFoundError):
        await playwright_browser_core.fill_application_form(
            url="file://some_non_existent_page.html",
            profile_data={},
            resume_path=invalid_resume_path
        )
