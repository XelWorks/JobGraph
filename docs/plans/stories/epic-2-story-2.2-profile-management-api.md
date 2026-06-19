# Story 2.2: Profile management API


**Must Read**:
- `docs/requirements.md` - Profile configuration details and resume storage

**Description**:
Create the candidate profile API supporting CRUD operations. Candidates must be able to specify their skills, education history, salary targets, and upload their master resume (persisted inside MinIO).

**Acceptance Criteria**:
- POST `/api/v1/profile` saves/updates profile fields (skills, locations, salary expectation).
- POST `/api/v1/profile/resume` accepts PDF/Docx upload and saves it to MinIO.
- Profile responses include signed, temporary pre-signed MinIO URL for the resume (valid for 15 minutes).
- Validation prevents empty skills lists or negative salary inputs.

**Prerequisites**:
- Story 2.1 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- Repository Pattern
- Secure Storage Isolation Pattern

**Implementation Steps**:
1. Create PostgreSQL schemas/models for UserProfile, Skills, and Experience.
2. Implement profile repository in `backend/app/infrastructure/db/profile_repository.py`.
3. Create API routes `POST/GET /api/v1/profile` and `POST /api/v1/profile/resume`.

**Test Requirements**:
- Integration tests saving profile data and uploading files to MinIO.
- Assert validation errors on missing/malformed inputs.

**Quality Checks**:
- Clean handling of binary payloads without memory ballooning.

**Out of Scope**:
- Automated parsing of resume content (LLM-based parsing).

**Completion Evidence**:
- Integration test scripts verifying PDF upload and file persistence in MinIO.
