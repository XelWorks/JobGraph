import json
import logging
import asyncio
from typing import Any, Dict

import httpx
from app.core.config import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

logger = logging.getLogger("app.services.tailoring.gemini")


class GeminiClient:
    """Wrapper service for interacting securely with Google Gemini API."""

    def __init__(self) -> None:
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.api_url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        )

    async def generate_tailored_resume_data(
        self,
        candidate_info: Dict[str, Any],
        job_title: str,
        job_company: str,
        job_description: str,
    ) -> Dict[str, Any]:
        """
        Send a structured prompt to Gemini API requesting customized resume details.
        Returns a structured dictionary representing the optimized candidate profile.
        """
        prompt = f"""
You are an expert executive resume writer and career coach specialized in optimizing resumes to pass ATS systems.
Your task is to customize the candidate's professional resume details to align perfectly with the target job posting.

Candidate Profile details:
- Name: {candidate_info.get("first_name", "Candidate")} {candidate_info.get("last_name", "Account")}
- Email: {candidate_info.get("email", "")}
- Phone: {candidate_info.get("phone", "")}
- Raw/Core Skills: {", ".join(candidate_info.get("skills", []))}
- Professional Experience: {json.dumps(candidate_info.get("experiences", []))}

Target Job Posting:
- Title: {job_title}
- Company: {job_company}
- Description: {job_description}

Instructions:
1. **Professional Summary**: Rewrite the candidate's professional summary. It should be highly compelling, tailored to highlight the candidate's matching skills, and aligned with the responsibilities in the job description. Keep it between 3 and 4 sentences.
2. **Core Skills**: Sort and select the most relevant skills. Prioritize skills specifically requested in the job description. Retain high-value candidate skills.
3. **Tailored Experience**: Iterate through the candidate's experiences. Retain exact company names, roles, and dates. For each experience, generate 3 to 4 tailored accomplishment bullet points. The bullets must:
   - Use strong action verbs at the beginning of each point.
   - Emphasize and integrate matching keywords from the job description.
   - Quantify results or describe impacts where applicable.
4. **Retain integrity**: Do not fabricate degrees or credentials. Keep the output factual, professional, and free of hype/buzzwords.

Your response must be a single, valid JSON object conforming exactly to this JSON schema:
{{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "phone number",
  "summary": "Compelling tailored summary text...",
  "skills": ["Skill 1", "Skill 2", "Skill 3", ...],
  "experience": [
    {{
      "company": "Company Name",
      "role": "Role Name",
      "dates": "Start Date - End Date",
      "bullets": [
        "Tailored bullet point 1 using strong action verbs...",
        "Tailored bullet point 2...",
        "Tailored bullet point 3..."
      ]
    }}
  ]
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
            logger.info("Using mock Gemini resume data due to unconfigured API key.")
            return self._get_mock_tailored_data(candidate_info, job_title, job_company)

        try:
            async with httpx.AsyncClient() as client:
                for attempt in range(2):
                    response = await client.post(self.api_url, json=payload, timeout=30.0)
                    if response.status_code == 200:
                        resp_json = response.json()
                        candidate_text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                        return json.loads(candidate_text)

                    if response.status_code not in {429, 500, 502, 503, 504}:
                        raise RuntimeError(f"Gemini API error (Status {response.status_code})")

                    logger.warning(
                        "gemini_resume_transient_error",
                        extra={"status_code": response.status_code, "attempt": attempt + 1},
                    )
                    if attempt == 0:
                        await asyncio.sleep(1)

            logger.warning("gemini_resume_unavailable_using_local_fallback")
            return self._get_mock_tailored_data(candidate_info, job_title, job_company)

        except httpx.HTTPError as e:
            logger.error(f"Gemini API request failed due to connectivity issues: {e}")
            return self._get_mock_tailored_data(candidate_info, job_title, job_company)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse structured Gemini output: {e}")
            return self._get_mock_tailored_data(candidate_info, job_title, job_company)

    def _get_mock_tailored_data(self, candidate_info: Dict[str, Any], job_title: str, job_company: str) -> Dict[str, Any]:
        """Fallback helper returning standard structured mock details when the API key is unconfigured."""
        name = f"{candidate_info.get('first_name', 'Candidate')} {candidate_info.get('last_name', 'Account')}"
        email = candidate_info.get("email", "candidate@example.com")
        phone = candidate_info.get("phone", "+1 (555) 019-2834")
        skills = candidate_info.get("skills", ["Python", "FastAPI", "React", "Docker"])

        raw_experiences = candidate_info.get("experiences", [])
        experience_list = []

        for exp in raw_experiences:
            company = exp.get("company", "Sample Corp")
            role = exp.get("role", "Software Engineer")
            dates = f"{exp.get('start_date', '2024')} - {exp.get('end_date', 'Present')}"

            experience_list.append({
                "company": company,
                "role": role,
                "dates": dates,
                "bullets": [
                    f"Architected and deployed backend platform architectures matching target {job_title} requirements.",
                    f"Partnered with cross-functional software teams at {job_company} to integrate performant services.",
                    "Optimized data querying pipelines reducing latency overheads by over 30%."
                ]
            })

        if not experience_list:
            experience_list.append({
                "company": "XelWorks",
                "role": "Senior Developer",
                "dates": "2024 - Present",
                "bullets": [
                    f"Led engineering cycles targeting core features matching {job_title} responsibilities.",
                    f"Leveraged skills in {', '.join(skills[:3])} to optimize delivery workflows at {job_company}.",
                    "Implemented responsive dashboards enhancing client visibility and interaction rates by 40%."
                ]
            })

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "summary": f"Highly motivated Professional specialized in applying advanced workflows matching the requirements of a {job_title} at {job_company}. Proven record of leveraging modern frameworks to optimize background pipelines, enhance security models, and deliver production-ready software systems.",
            "skills": skills,
            "experience": experience_list
        }

    async def generate_tailored_cover_letter_data(
        self,
        candidate_info: Dict[str, Any],
        job_title: str,
        job_company: str,
        job_description: str,
    ) -> Dict[str, Any]:
        """
        Send a structured prompt to Gemini API requesting a tailored cover letter.
        Returns a structured dictionary with subject and body of the cover letter.
        """
        prompt = f"""
You are an expert executive career coach and recruiter.
Your task is to write a highly compelling, professional cover letter for the candidate applying to the target job posting.

Candidate Profile details:
- Name: {candidate_info.get("first_name", "Candidate")} {candidate_info.get("last_name", "Account")}
- Email: {candidate_info.get("email", "")}
- Phone: {candidate_info.get("phone", "")}
- Raw/Core Skills: {", ".join(candidate_info.get("skills", []))}
- Professional Experience: {json.dumps(candidate_info.get("experiences", []))}

Target Job Posting:
- Title: {job_title}
- Company: {job_company}
- Description: {job_description}

Instructions:
1. Write a professional 3-to-4 paragraph cover letter.
2. The letter should include:
   - A polite salutation to the Hiring Manager.
   - An engaging opening paragraph expressing high-fidelity interest in the specific {job_title} role at {job_company}.
   - 1-2 body paragraphs seamlessly integrating the candidate's core matching skills and experiences.
   - A concluding paragraph with a professional call to action.
   - A formal closing and signature line.
3. Do not fabricate degrees or experience. Keep it highly aligned and professional.

Your response must be a single, valid JSON object conforming exactly to this JSON schema:
{{
  "subject": "Application for {job_title} at {job_company}",
  "body": "Dear Hiring Team,\\n\\nI am writing to express my strong interest in...\\n\\nSincerely,\\n\\n{candidate_info.get("first_name", "Candidate")} {candidate_info.get("last_name", "Account")}"
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
            logger.info("Using mock Gemini cover letter data due to unconfigured API key.")
            return self._get_mock_cover_letter_data(candidate_info, job_title, job_company)

        try:
            async with httpx.AsyncClient() as client:
                for attempt in range(2):
                    response = await client.post(self.api_url, json=payload, timeout=30.0)
                    if response.status_code == 200:
                        resp_json = response.json()
                        candidate_text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                        return json.loads(candidate_text)

                    if response.status_code not in {429, 500, 502, 503, 504}:
                        raise RuntimeError(f"Gemini API error (Status {response.status_code})")

                    logger.warning(
                        "gemini_cover_letter_transient_error",
                        extra={"status_code": response.status_code, "attempt": attempt + 1},
                    )
                    if attempt == 0:
                        await asyncio.sleep(1)

            logger.warning("gemini_cover_letter_unavailable_using_local_fallback")
            return self._get_mock_cover_letter_data(candidate_info, job_title, job_company)

        except httpx.HTTPError as e:
            logger.error(f"Gemini API request failed due to connectivity issues: {e}")
            return self._get_mock_cover_letter_data(candidate_info, job_title, job_company)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse structured Gemini cover letter output: {e}")
            return self._get_mock_cover_letter_data(candidate_info, job_title, job_company)

    def _get_mock_cover_letter_data(self, candidate_info: Dict[str, Any], job_title: str, job_company: str) -> Dict[str, Any]:
        """Fallback helper returning standard structured mock cover letter details when the API key is unconfigured."""
        name = f"{candidate_info.get('first_name', 'Candidate')} {candidate_info.get('last_name', 'Account')}"
        email = candidate_info.get("email", "candidate@example.com")
        phone = candidate_info.get("phone", "+1 (555) 019-2834")
        skills = candidate_info.get("skills", ["Python", "FastAPI", "React", "Docker"])

        subject = f"Application for {job_title} at {job_company}"
        body = (
            f"Dear Hiring Team,\n\n"
            f"I am writing to express my strong interest in the {job_title} position at {job_company}. "
            f"With a robust background as a software engineer and proven expertise in {', '.join(skills[:3])}, "
            f"I am confident in my ability to deliver high-quality, scalable contributions to your engineering organization.\n\n"
            f"Throughout my career, I have specialized in architecting responsive systems and performant APIs. "
            f"I am eager to align my experiences with the core objectives outlined in your job posting and help drive "
            f"success on {job_company}'s initiatives.\n\n"
            f"Thank you for your time and consideration. I welcome the opportunity to discuss my qualifications further.\n\n"
            f"Sincerely,\n\n"
            f"{name}\n"
            f"{email} | {phone}"
        )

        return {
            "subject": subject,
            "body": body
        }


def generate_pdf_resume(resume_data: Dict[str, Any], output_path: str) -> None:
    """
    Renders structured resume JSON payload details into a professional minimalist text PDF.
    Saves the PDF output to the specified output_path.
    """
    # Create the document template with standard minimalist margins
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Define professional typography sizes and colors
    primary_color = colors.HexColor("#0f172a")  # Slate 900
    accent_color = colors.HexColor("#0284c7")   # Sky 600
    text_color = colors.HexColor("#334155")     # Slate 700

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=primary_color,
        alignment=1,  # Center
        spaceAfter=4
    )

    contact_style = ParagraphStyle(
        "DocContact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=text_color,
        alignment=1,  # Center
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        "DocH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=accent_color,
        spaceBefore=12,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=text_color,
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        "DocBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=text_color,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    exp_title_style = ParagraphStyle(
        "DocExpTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=primary_color,
        spaceBefore=4,
        keepWithNext=True
    )

    exp_meta_style = ParagraphStyle(
        "DocExpMeta",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=text_color,
        alignment=2,  # Right align dates
        spaceBefore=4
    )

    story = []

    # 1. Header Name and Contacts
    story.append(Paragraph(resume_data.get("name", "Candidate"), title_style))
    contact_text = f"{resume_data.get('email', '')}  |  {resume_data.get('phone', '')}"
    story.append(Paragraph(contact_text, contact_style))

    # 2. Professional Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", h1_style))
    story.append(Paragraph(resume_data.get("summary", ""), body_style))
    story.append(Spacer(1, 4))

    # 3. Core Skills
    story.append(Paragraph("CORE SKILLS", h1_style))
    skills_list = resume_data.get("skills", [])
    skills_text = " • ".join(skills_list)
    story.append(Paragraph(skills_text, body_style))
    story.append(Spacer(1, 4))

    # 4. Professional Experience
    story.append(Paragraph("PROFESSIONAL EXPERIENCE", h1_style))

    for exp in resume_data.get("experience", []):
        # Format Company/Role and Dates side-by-side using Table
        left_p = Paragraph(f"<b>{exp.get('company', '')}</b> — {exp.get('role', '')}", exp_title_style)
        right_p = Paragraph(exp.get("dates", ""), exp_meta_style)

        meta_table = Table([[left_p, right_p]], colWidths=[380, 150])
        meta_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
        ]))

        story.append(meta_table)
        story.append(Spacer(1, 2))

        # Experience bullet items
        for bullet in exp.get("bullets", []):
            story.append(Paragraph(f"&bull; {bullet}", bullet_style))

        story.append(Spacer(1, 4))

    # Build document
    doc.build(story)


def generate_pdf_cover_letter(cover_letter_data: Dict[str, Any], output_path: str) -> None:
    """
    Renders structured cover letter JSON payload details into a professional minimalist text PDF.
    Saves the PDF output to the specified output_path.
    """
    # Create the document template with standard minimalist margins
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Define professional typography sizes and colors
    accent_color = colors.HexColor("#0284c7")   # Sky 600
    text_color = colors.HexColor("#334155")     # Slate 700

    subject_style = ParagraphStyle(
        "CLSubject",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=accent_color,
        spaceBefore=10,
        spaceAfter=15,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "CLBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=text_color,
        spaceAfter=10
    )

    story = []

    # Subject line
    subject_text = cover_letter_data.get("subject", "Job Application")
    story.append(Paragraph(f"<b>Subject:</b> {subject_text}", subject_style))

    # Body paragraphs - split by newlines and render
    body_text = cover_letter_data.get("body", "")
    # Split by newline groups (preserving structure, but converting newlines into <br/> or multiple paragraphs)
    raw_paragraphs = body_text.split("\n\n")
    for para in raw_paragraphs:
        para_clean = para.strip()
        if para_clean:
            # Replace internal single newlines with break lines
            formatted_text = para_clean.replace("\n", "<br/>")
            story.append(Paragraph(formatted_text, body_style))

    # Build document
    doc.build(story)

