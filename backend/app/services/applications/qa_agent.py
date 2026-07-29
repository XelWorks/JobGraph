# ruff: noqa: C901
import json
import logging
from typing import Any, Dict, List

import httpx
from app.core.config import settings

logger = logging.getLogger("app.services.applications.qa_agent")


class QAAgentService:
    """Wrapper service using Gemini to answer custom, dynamic recruiter questions on forms based on candidate profiles."""

    def __init__(self) -> None:
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.api_url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        )

    async def answer_custom_question(
        self,
        question_text: str,
        field_type: str,  # "text", "textarea", "select", "radio", "checkbox"
        options: List[str],  # empty for text/textarea
        candidate_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Interacts with Gemini to generate a tailored, professional response for custom recruiter questions.
        Returns a structured dictionary:
        {
          "answer_text": "text value or selected option",
          "matched_option_index": int (for select/radio),
          "boolean_value": bool (for checkboxes)
        }
        """
        # System Prompt
        prompt = f"""
You are an expert recruiter and career agent assisting a candidate in auto-filling custom questions on a job application.
Your goal is to answer the target question accurately, professionally, and factually, using only the candidate's profile details.

Candidate Profile details:
- Name: {candidate_profile.get("first_name", "Candidate")} {candidate_profile.get("last_name", "Account")}
- Email: {candidate_profile.get("email", "")}
- Phone: {candidate_profile.get("phone", "")}
- Preferred Roles: {", ".join(candidate_profile.get("preferred_roles", []))}
- Target Salary: ${candidate_profile.get("target_salary", 0)}
- Preferred Locations: {", ".join(candidate_profile.get("preferred_locations", []))}
- Skills: {", ".join(candidate_profile.get("skills", []))}
- Work Experience: {json.dumps(candidate_profile.get("experiences", []))}

Target Question Details:
- Question Text: "{question_text}"
- HTML Input Field Type: "{field_type}"
- List of Options available on form: {json.dumps(options)}

Instructions:
1. **Fact-First**: Do not fabricate degrees, citizenship status, or experience years. If profile does not contain details, make a highly professional, conservative, standard estimate or answer politely (e.g. for text fields, write a concise standard statement).
2. **Field Types rules**:
   - If `field_type` is "select" or "radio", select the absolute best matching string from the `options` array, and specify its 0-based index in `matched_option_index`.
   - If `field_type` is "checkbox", determine if the candidate's answer should be `True` or `False` in `boolean_value`.
   - If `field_type` is "text" or "textarea", write a concise, professional answer in `answer_text` (under 2-3 sentences unless asked otherwise).
3. **No Hype**: Keep answers objective, formal, and matching corporate tones.

Your response must be a single, valid JSON object conforming exactly to this JSON schema:
{{
  "answer_text": "Answer text here",
  "matched_option_index": -1,
  "boolean_value": false
}}
"""

        # Prepare request payload with generationConfig forcing JSON output
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        # Handle mock/testing modes or empty keys gracefully
        if not self.api_key or self.api_key == "mock-key-for-now":
            logger.info("Using mock Gemini custom question answering due to unconfigured API key.")
            return self._get_mock_qa_response(question_text, field_type, options, candidate_profile)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, json=payload, timeout=25.0)

                if response.status_code != 200:
                    logger.error(f"Gemini API QA error: status_code={response.status_code}, body={response.text}")
                    raise RuntimeError(f"Gemini API error (Status {response.status_code})")

                resp_json = response.json()
                answer_text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(answer_text)

        except httpx.HTTPError as e:
            logger.error(f"Gemini API request failed in QAAgentService: {e}")
            raise RuntimeError("Gemini API connection timeout or limit reached.") from e
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse structured Gemini QA output: {e}")
            return self._get_mock_qa_response(question_text, field_type, options, candidate_profile)

    def _get_mock_qa_response(
        self,
        question_text: str,
        field_type: str,
        options: List[str],
        candidate_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback mock QA selector for offline testing and configuration failures."""
        q_lower = question_text.lower()

        answer_text = ""
        matched_option_index = -1
        boolean_value = False

        if field_type in ["select", "radio"]:
            # Pick a default option matching common questions
            if "authorized" in q_lower or "sponsorship" in q_lower or "visa" in q_lower:
                # E.g. "Are you authorized to work?" -> options = ["Yes", "No"]
                # Default to Yes for authorized, No for visa help
                for i, opt in enumerate(options):
                    o_lower = opt.lower()
                    if "yes" in o_lower and "sponsorship" not in q_lower:
                        matched_option_index = i
                        answer_text = opt
                        break
                    elif "no" in o_lower and "sponsorship" in q_lower:
                        matched_option_index = i
                        answer_text = opt
                        break
            if matched_option_index == -1 and options:
                # Default to first option
                matched_option_index = 0
                answer_text = options[0]

        elif field_type == "checkbox":
            if "authorized" in q_lower or "accept" in q_lower:
                boolean_value = True

        else:
            # text or textarea
            if "experience" in q_lower or "years" in q_lower:
                if "python" in q_lower:
                    answer_text = "I have approximately 3 years of experience writing clean, scalable Python backend code."
                else:
                    answer_text = "I have over 3 years of experience in modern software engineering and cloud deployments."
            elif "salary" in q_lower:
                target = candidate_profile.get("target_salary", 0)
                answer_text = f"${target:,}" if target > 0 else "My salary expectations are aligned with market rates."
            else:
                answer_text = "I am highly aligned with this position and excited to bring my engineering background to the team."

        return {
            "answer_text": answer_text,
            "matched_option_index": matched_option_index,
            "boolean_value": boolean_value
        }


qa_agent_service = QAAgentService()
