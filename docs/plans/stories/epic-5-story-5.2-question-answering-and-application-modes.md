# Story 5.2: Question answering and application modes

**Developer**: Dev 1

**Must Read**:
- `docs/requirements.md` - Form submission execution modes (Manual, Assisted, Autonomous)

**Description**:
Implement QA logic using Gemini to extract context and answer custom recruiter questions on forms. Build the three execution modes: Manual (materials compile), Assisted (auto-fill, wait for click), and Autonomous (complete submission).

**Acceptance Criteria**:
- Generates answers for custom form inputs (e.g. "Work eligibility", "Years of experience").
- Assisted mode fills the form, stops browser headless state, and prompts the user for review.
- Autonomous mode fills, submits, and records success logs.

**Prerequisites**:
- Story 5.1 and 2.2 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- Clean architecture workflows

**Implementation Steps**:
1. Write custom QA matching services `backend/app/services/applications/qa_agent.py`.
2. Integrate LLM parsing logic for custom dropdowns/radio fields.
3. Control Playwright submission triggers by execution modes.

**Test Requirements**:
- Assert questions match profile answers in mock tests.

**Quality Checks**:
- Form submissions check required states first.

**Out of Scope**:
- Capcha bypassing.

**Completion Evidence**:
- Successful validation test scripts.