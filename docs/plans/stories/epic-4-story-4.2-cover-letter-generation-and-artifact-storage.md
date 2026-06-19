# Story 4.2: Cover letter generation and artifact storage

**Developer**: Dev 1

**Must Read**:
- `docs/requirements.md` - Cover letter requirements and storage constraints

**Description**:
Implement cover letter generation using Gemini, and save both tailored resumes and cover letters in MinIO storage buckets mapping to the specific application record.

**Acceptance Criteria**:
- Generates tailored cover letters highlighting aligned skills.
- Stores files inside dedicated MinIO directories (`resumes/`, `cover_letters/`).
- Database records link the application record to the uploaded artifacts.

**Prerequisites**:
- Story 4.1 and 1.3 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- Repository transactions, storage isolations

**Implementation Steps**:
1. Implement cover letter prompt and generation services.
2. Implement S3 save logic in `backend/app/infrastructure/storage/artifacts.py`.
3. Update Application model schema to reference resume/cover letter URLs.

**Test Requirements**:
- Verification that generated files exist in the mock/local S3 buckets.

**Quality Checks**:
- Nonces or random UUID file path prefixes to prevent path traversal/overwrite leaks.

**Out of Scope**:
- UI forms (UI is handled next).

**Completion Evidence**:
- Pytest assertions confirming files are stored in S3 and path keys saved in DB.