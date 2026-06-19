# Story 2.4: Auth/profile integration test

**Developer**: Dev 1

**Must Read**:
- `docs/architecture/design/00-system-architecture-greenfield.md` - Layer verification

**Description**:
Create a complete integration test validation script targeting registration, login authentication, profile updates, and file uploads. It asserts layer coordination between the API, db, and storage.

**Acceptance Criteria**:
- Test script executes automatically via `pytest`.
- Registers a test user, verifies hashed DB pass, logs in, obtains JWT, updates profile details, and uploads a sample PDF.
- Verifies uploaded PDF was stored correctly in MinIO.

**Prerequisites**:
- Story 2.1, 2.2, 2.3 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- Integration Test Pattern (AAA)

**Implementation Steps**:
1. Write testing script in `backend/tests/integration/test_auth_profile.py`.
2. Configure test client sessions and local test environment overrides.

**Test Requirements**:
- The script must assert 200 OK responses, data match in DB, and file presence in S3 bucket.

**Quality Checks**:
- Clean up test data (user record, S3 file) after test execution.

**Out of Scope**:
- Mocking network interfaces; must use actual local database and MinIO.

**Completion Evidence**:
- Console output of successful pytest integration tests.