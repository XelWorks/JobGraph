# Story 5.1: Application execution browser core

**Developer**: Dev 2

**Must Read**:
- `docs/requirements.md` - Playwright automation requirements
- `docs/architecture/design/00-system-architecture-greenfield.md` - Playwright sandboxing

**Description**:
Build the Playwright headless browser core handler to navigate job application pages, locate standard form fields (First Name, Last Name, Email, Resume Upload), and input profile data.

**Acceptance Criteria**:
- Playwright client opens headless browsers and accesses forms.
- Automatically handles Greenhouse and Lever input structures.
- Uploads custom documents (tailored resumes) to form upload inputs.
- Handles element waits and page errors.

**Prerequisites**:
- Story 4.1, 4.2, 1.3 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- Playwright page interactions wrapper

**Implementation Steps**:
1. Implement Playwright adapter client in `backend/app/infrastructure/browser/playwright_client.py`.
2. Write selector parsing maps for common fields.

**Test Requirements**:
- Run Playwright against local HTML mock forms (Greenhouse/Lever mock styles).
- Assert fields are filled and files uploaded.

**Quality Checks**:
- Browser instance closes gracefully in all cases (including exceptions).

**Out of Scope**:
- Answering custom/complex recruiter questions.

**Completion Evidence**:
- Local browser test scripts passing.