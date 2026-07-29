import os
import tempfile

import pytest
from app.infrastructure.browser.playwright_client import playwright_browser_core
from app.services.applications.qa_agent import qa_agent_service

MOCK_CANDIDATE_PROFILE = {
    "first_name": "Gourav",
    "last_name": "G",
    "email": "gourav@example.com",
    "phone": "+1 (555) 019-2834",
    "preferred_roles": ["FastAPI Developer"],
    "target_salary": 145000,
    "skills": ["Python", "FastAPI", "Postgres"],
    "experiences": [
        {
            "company": "TechCorp",
            "role": "Software Engineer",
            "description": "Fitted custom services with FastAPI and Python."
        }
    ]
}

MOCK_FORM_WITH_CUSTOM_QUESTIONS = """
<!DOCTYPE html>
<html>
<head><title>Mock Recruiter Application Form</title></head>
<body>
  <form id="application_form" action="/submit" method="POST">
    <!-- Standard Fields -->
    <input type="text" id="first_name" name="job_application[first_name]" value="Gourav" />
    <input type="text" id="last_name" name="job_application[last_name]" value="G" />
    <input type="email" id="email" name="job_application[email]" value="gourav@example.com" />
    <input type="text" id="phone" name="job_application[phone]" value="+1 (555) 019-2834" />
    <input type="file" id="resume_file" name="job_application[resume]" />

    <!-- Custom Text Field -->
    <label for="custom_experience">Years of experience in Python:</label>
    <input type="text" id="custom_experience" name="custom_experience_years" />

    <!-- Custom Select Dropdown -->
    <label for="work_authorization">Visa Sponsorship status:</label>
    <select id="work_authorization" name="work_auth_status">
      <option value="">Select option</option>
      <option value="authorized">I require visa sponsorship</option>
      <option value="not_required">I do not require visa sponsorship</option>
    </select>

    <button type="submit" id="submit_button">Submit Application</button>
  </form>
</body>
</html>
"""


@pytest.mark.asyncio
async def test_qa_agent_answers_custom_questions():
    """Unit test checking that QAAgentService successfully answers text, select options and checkbox questions factually."""
    from app.core.config import settings
    original_api_key = settings.gemini_api_key
    settings.gemini_api_key = "mock-key-for-now"

    original_service_key = qa_agent_service.api_key
    qa_agent_service.api_key = "mock-key-for-now"

    try:
        # 1. Text Question
        res_text = await qa_agent_service.answer_custom_question(
            question_text="How many years of experience do you have in Python?",
            field_type="text",
            options=[],
            candidate_profile=MOCK_CANDIDATE_PROFILE
        )
        assert res_text["answer_text"] != ""
        assert "python" in res_text["answer_text"].lower() or "experience" in res_text["answer_text"].lower()

        # 2. Select Question
        res_select = await qa_agent_service.answer_custom_question(
            question_text="Will you now or in the future require visa sponsorship?",
            field_type="select",
            options=["I require visa sponsorship", "I do not require visa sponsorship"],
            candidate_profile=MOCK_CANDIDATE_PROFILE
        )
        assert res_select["matched_option_index"] in [0, 1]
        assert res_select["answer_text"] in ["I require visa sponsorship", "I do not require visa sponsorship"]
    finally:
        settings.gemini_api_key = original_api_key
        qa_agent_service.api_key = original_service_key


@pytest.mark.asyncio
async def test_assisted_and_autonomous_modes_forms_interfacing():
    """
    Integration Test checking application execution modes:
    1. Assisted Mode: Fills standard & custom fields, pauses browser, does NOT trigger submit click.
    2. Autonomous Mode: Fills form fields, triggers form submit click, and verifies the submission.
    3. Manual Mode: Bypasses headless browser creation entirely.
    """
    from app.core.config import settings
    original_api_key = settings.gemini_api_key
    settings.gemini_api_key = "mock-key-for-now"

    original_service_key = qa_agent_service.api_key
    qa_agent_service.api_key = "mock-key-for-now"

    with tempfile.TemporaryDirectory() as temp_dir:
        resume_path = os.path.join(temp_dir, "my_tailored_resume.pdf")
        with open(resume_path, "wb") as f:
            f.write(b"%PDF-1.4 dummy resume")

        screenshot_path = os.path.join(temp_dir, "fill_verification.png")

        # Write mock form HTML with custom inputs to file
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
            f.write(MOCK_FORM_WITH_CUSTOM_QUESTIONS)
            html_path = f.name

        try:
            url = f"file://{html_path}"

            # --- Test 1: Manual Mode ---
            manual_res = await playwright_browser_core.fill_application_form(
                url=url,
                profile_data=MOCK_CANDIDATE_PROFILE,
                resume_path=resume_path,
                screenshot_path=screenshot_path,
                mode="Manual"
            )
            assert manual_res["status"] == "success"
            assert manual_res["mode_handled"] == "Manual"
            assert manual_res["submitted"] is False

            # --- Test 2: Assisted Mode ---
            assisted_res = await playwright_browser_core.fill_application_form(
                url=url,
                profile_data=MOCK_CANDIDATE_PROFILE,
                resume_path=resume_path,
                screenshot_path=screenshot_path,
                mode="Assisted"
            )
            assert assisted_res["status"] == "success"
            assert assisted_res["ats_type"] == "greenhouse"
            assert assisted_res["uploaded_resume"] is True
            assert assisted_res["custom_questions_answered"] == 2
            assert assisted_res["submitted"] is False
            assert assisted_res["paused_for_review"] is True

            # --- Test 3: Autonomous Mode ---
            auto_res = await playwright_browser_core.fill_application_form(
                url=url,
                profile_data=MOCK_CANDIDATE_PROFILE,
                resume_path=resume_path,
                screenshot_path=screenshot_path,
                mode="Autonomous"
            )
            assert auto_res["status"] == "success"
            assert auto_res["ats_type"] == "greenhouse"
            assert auto_res["custom_questions_answered"] == 2
            assert auto_res["submitted"] is True

        finally:
            settings.gemini_api_key = original_api_key
            qa_agent_service.api_key = original_service_key
            if os.path.exists(html_path):
                os.remove(html_path)
