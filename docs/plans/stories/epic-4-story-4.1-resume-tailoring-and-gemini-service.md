# Story 4.1: Resume tailoring and Gemini service


**Must Read**:
- `docs/requirements.md` - Resume tailoring requirements
- `docs/architecture/design/00-system-architecture-greenfield.md` - LLM integration

**Description**:
Integrate Google Gemini API to parse job descriptions, compare them to the candidate's master resume, and generate tailored, ATS-optimized resume details.

**Acceptance Criteria**:
- Service sends structured prompts containing master resume and JD to Gemini API.
- Receives structured responses outlining adjusted bullet points.
- Outputs are rendered into a professional PDF format.
- Securely processes API keys from configurations.

**Prerequisites**:
- Story 3.2, 2.2, 1.3 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- Safe APIs and keys loading

**Implementation Steps**:
1. Setup Gemini client wrapper in `backend/app/services/tailoring/gemini.py`.
2. Design prompt template for resume optimization.
3. Integrate a basic python PDF generation helper to output PDFs.

**Test Requirements**:
- Unit test mock Gemini API calls.
- Assert PDF output exists and is populated with text.

**Quality Checks**:
- Graceful API error handling (timeouts, quota limits).

**Out of Scope**:
- Direct PDF layout designer; default to clean, minimalist text template.

**Completion Evidence**:
- Successful generation of tailored PDF during test runs.
