# Story 3.4: Scheduled discovery integration test


**Must Read**:
- `docs/architecture/design/00-system-architecture-greenfield.md` - Background operations

**Description**:
Create the integration test suite validating job crawler runs, scoring, deduplication database states, and updates to the frontend API outputs.

**Acceptance Criteria**:
- Test triggers discovery crawler mock routines.
- Verifies new jobs are created, duplicates are skipped, and scores are populated.
- Confirms output is served correctly to `/api/v1/jobs` endpoints.

**Prerequisites**:
- Story 3.1, 3.2, 3.3 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- Integration test standards (AAA)

**Implementation Steps**:
1. Create `backend/tests/integration/test_discovery.py`.
2. Run database state assertions after mock crawling cycles.

**Test Requirements**:
- Assert final database counts, duplicate rejection events, and JSON format endpoints.

**Quality Checks**:
- Clean up test entries from tables post-run.

**Out of Scope**:
- Mocking browser UI clicks.

**Completion Evidence**:
- Pytest command console reports showing 100% pass on crawler tests.
