# Story 2.3: Auth and profile UI


**Must Read**:
- `docs/requirements.md` - Next.js dashboard expectations

**Description**:
Create user forms for authentication (Login/Register) and the main Profile page where the candidate configures experience, uploads resumes, and configures salary preferences.

**Acceptance Criteria**:
- Login form sends data to API and stores JWT in cookies/localStorage.
- Profile page contains editable forms for all profile fields.
- Drag-and-drop file uploader component handles PDF/Docx uploads.
- Displays uploaded resume filename and status.

**Prerequisites**:
- Story 1.2 and 2.2 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- Next.js page layouts and forms with clean UX styling.

**Implementation Steps**:
1. Create Login and Register components in `frontend/features/auth/`.
2. Create profile forms and file upload wrapper in `frontend/features/profiles/`.
3. Route pages in `frontend/app/login/` and `frontend/app/profile/`.

**Test Requirements**:
- Mocking backend API checks client submission states.
- Checking upload triggers correct client API requests.

**Quality Checks**:
- Responsive interface and validation checks on email inputs.

**Out of Scope**:
- Multiple candidate logins (v0.1 is single-user).

**Completion Evidence**:
- Local frontend compilation logs and verified form displays.
