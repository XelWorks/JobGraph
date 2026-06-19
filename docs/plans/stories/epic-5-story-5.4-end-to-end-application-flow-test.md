# Story 5.4: End-to-end application flow test

**Developer**: Dev 1

**Must Read**:
- `docs/architecture/design/00-system-architecture-greenfield.md` - Verification

**Description**:
Build the full flow integration test that runs the discovery connector, scores the job, tailors the document, stores it in MinIO, fills the form via Playwright, and updates database records.

**Acceptance Criteria**:
- Test executes cleanly against mock ATS servers.
- Database records updated to 'Submitted' status.
- Resumes are validated to have been customized.

**Prerequisites**:
- Story 5.1, 5.2, 5.3 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- Integration test structures

**Implementation Steps**:
1. Implement `backend/tests/integration/test_application_flow.py`.
2. Configure mock static servers simulating ATS portals.

**Test Requirements**:
- Assertions checking DB state transitions, file creation, and Playwright execution paths.

**Quality Checks**:
- Isolated DB tables and MinIO buckets reset post-test.

**Out of Scope**:
- Real submission endpoints (always use mock targets for testing).

**Completion Evidence**:
- Integration test suite console report.