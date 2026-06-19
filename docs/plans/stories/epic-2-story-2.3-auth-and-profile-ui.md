# Story 2.3: Auth and profile UI

**Developer**: Dev 2

**Must Read**:
- `docs/requirements.md` - React JS dashboard expectations

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
- React JS page layouts and forms with clean UX styling.

**Implementation Steps**:
1. Create Login and Register components in `frontend/src/features/auth/`.
2. Create profile forms and file upload wrapper in `frontend/src/features/profiles/`.
3. Setup routing for `/login` and `/profile` pages.

**Test Requirements**:
- Mocking backend API checks client submission states.
- Checking upload triggers correct client API requests.

**Quality Checks**:
- Responsive interface and validation checks on email inputs.

**Out of Scope**:
- Multiple candidate logins (v0.1 is single-user).

**Completion Evidence**:
- Local frontend compilation logs and verified form displays.

---

## Change log

### 2026-06-19 — Updated for technical-constraints@v1.1

**Trigger:** drift run; entry-mode 2A plain-English.
**Pre-edit status:** planned   ← R14(b) carve-out

**Sections modified:**
- `## Must Read` — Updated reference expectations to React JS.
- `## Patterns to Follow` — Updated page layout references.
- `## Implementation Steps` — Refactored routing step.

**Delta:**

| Aspect | Before | After |
| :-- | :-- | :-- |
| Page Routing | File-system routing (`frontend/app/`) | Client-side routing (`react-router-dom`) |

**Reason no CR was drafted:** foundation story was `status: planned` at edit time (R14(b) carve-out — no shipped or in-flight code to preserve).