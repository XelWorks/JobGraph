# Story 9.4: Worker Queue Integration Test

**BUILDID**: NO-CYCLE | **Epic**: 9 - STANDALONE BROWSER WORKER & EVENT-BASED AUTOMATION | **ID**: 9.4 | **Date**: 2026-07-29 | **Jira**: LOCAL  
**Wave**: 17 | **Requires**: [9.1, 9.2] | **Enables**: [10.3]  
**Files Touched**: `backend/tests/integration/test_worker_queue.py`  
**Roles Ref**: Candidate  
**QA Candidate**: Yes — Observable: Valkey queue task pop and event emission; Mechanism: Pytest integration test; Authz & preconditions: Local Valkey instance; Edge & idempotency: Worker task completion and database state updates; Regression: Background worker processing.

---

## 👤 User Reference

### Description
Create an integration test verifying Valkey task queue processing, standalone browser worker execution, and event emission.

### Acceptance Criteria
- Pytest script pushes an application task to Valkey queue.
- Worker process pops task, executes Playwright filling, and emits lifecycle events.
- Asserts database application record status updates cleanly.

---

## 🤖 AI Agent Reference

### Context Files to Read
- `docs/architecture/design/00-system-architecture-greenfield.md`
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

### QA-Observable Behaviour
- `test_worker_queue.py` passes 100% of assertions for Valkey queue processing and event handling.

### Prerequisites
- Story 9.1 and Story 9.2 completed.

### Implementation Steps

1. **Create Integration Test (`backend/tests/integration/test_worker_queue.py`)**:
   - Push task to Valkey queue.
   - Run worker task handler.
   - Assert event emissions and database state changes.

### Test Requirements
- Run `pytest backend/tests/integration/test_worker_queue.py` and verify pass.

### Completion Evidence
- Pytest console output showing clean pass.
