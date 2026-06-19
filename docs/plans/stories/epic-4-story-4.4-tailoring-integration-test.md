# Story 4.4: Tailoring integration test


**Must Read**:
- `docs/architecture/design/00-system-architecture-greenfield.md` - Layer verification

**Description**:
Create a validation test confirming the complete document tailoring flow: profile configuration -> job details -> Gemini logic -> PDF compilation -> MinIO save -> secure link generation.

**Acceptance Criteria**:
- Pytest script runs and confirms all components of the tailoring pipeline connect.
- Asserts documents are generated, stored, and downloadable.

**Prerequisites**:
- Story 4.1, 4.2, 4.3 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- Integration test rules

**Implementation Steps**:
1. Create `backend/tests/integration/test_tailoring.py`.
2. Setup database/MinIO parameters and run full simulation cycle.

**Test Requirements**:
- Execute integration tests successfully with mock Gemini responses.

**Quality Checks**:
- Cleanup generated files after test.

**Out of Scope**:
- Scraping job inputs.

**Completion Evidence**:
- Integration pytest output reports.
