import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from app.services.tailoring.gemini import GeminiClient, generate_pdf_resume

# --- MOCK DETAILS ---

MOCK_CANDIDATE_INFO = {
    "first_name": "Alice",
    "last_name": "Smith",
    "email": "alice@example.com",
    "phone": "+1 (555) 901-2345",
    "skills": ["Python", "FastAPI", "Postgres"],
    "experiences": [
        {
            "company": "Tech Corp",
            "role": "Senior Engineer",
            "start_date": "2023",
            "end_date": "Present"
        }
    ]
}

MOCK_TAILORED_STRUCTURED_RESPONSE = {
    "name": "Alice Smith",
    "email": "alice@example.com",
    "phone": "+1 (555) 901-2345",
    "summary": "Tailored expert summary highlighting Python, FastAPI and Postgres capabilities for the Senior backend developer role.",
    "skills": ["Python", "FastAPI", "Postgres", "Docker"],
    "experience": [
        {
            "company": "Tech Corp",
            "role": "Senior Engineer",
            "dates": "2023 - Present",
            "bullets": [
                "Led design of high performance backend pipelines using Python and FastAPI.",
                "Optimized database indexing schemas on Postgres systems reducing latency by 45%.",
                "Deployed secure and performant microservices within lightweight Docker containers."
            ]
        }
    ]
}


@pytest.mark.asyncio
async def test_gemini_client_wrapper_api_mock():
    """Verify Gemini client correctly formats prompts and processes structured API responses."""
    client = GeminiClient()

    # 1. Force use of a real API key mock path (bypass self-mocking check)
    client.api_key = "AIza_mock_api_key_for_testing"
    client.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={client.api_key}"

    mock_resp = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": '{"name": "Alice Smith", "email": "alice@example.com", "phone": "+1 (555) 901-2345", "summary": "Tailored summary", "skills": ["Python"], "experience": []}'}
                    ]
                }
            }
        ]
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_resp
        mock_post.return_value = mock_response

        res = await client.generate_tailored_resume_data(
            candidate_info=MOCK_CANDIDATE_INFO,
            job_title="Senior Developer",
            job_company="InnovateLLC",
            job_description="Needs high-fidelity Python and FastAPI expertise."
        )

        assert res["name"] == "Alice Smith"
        assert res["summary"] == "Tailored summary"
        assert "Python" in res["skills"]
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_gemini_client_wrapper_fallback_if_no_key():
    """Verify Gemini client gracefully triggers high-fidelity fallback mocks when API key is default."""
    client = GeminiClient()
    client.api_key = "mock-key-for-now"  # default unconfigured status

    res = await client.generate_tailored_resume_data(
        candidate_info=MOCK_CANDIDATE_INFO,
        job_title="Senior Developer",
        job_company="InnovateLLC",
        job_description="Needs high-fidelity Python and FastAPI expertise."
    )

    assert res["name"] == "Alice Smith"
    assert "InnovateLLC" in res["summary"] or "Senior Developer" in res["summary"]
    assert "Python" in res["skills"]
    assert len(res["experience"]) == 1


def test_pdf_compilation():
    """Verify ReportLab compiles structured resume JSON payload details into a valid non-empty PDF file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_pdf_path = os.path.join(temp_dir, "tailored_resume.pdf")

        # Act
        generate_pdf_resume(MOCK_TAILORED_STRUCTURED_RESPONSE, output_pdf_path)

        # Assert
        assert os.path.exists(output_pdf_path)
        file_size = os.path.getsize(output_pdf_path)
        assert file_size > 0  # Confirms compiling succeeded and output file is populated with binary data

        # Verify it has PDF header bytes
        with open(output_pdf_path, "rb") as f:
            header = f.read(4)
            assert header == b"%PDF"
