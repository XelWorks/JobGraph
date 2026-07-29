# Story 10.3: End-to-End Interactive Control & Replay Test

**BUILDID**: NO-CYCLE | **Epic**: 10 - INTERACTIVE CONTROL & JOB REPLAY AUDIT | **ID**: 10.3 | **Date**: 2026-07-29 | **Jira**: LOCAL  
**Wave**: 19 | **Requires**: [10.1, 10.2, 9.4] | **Enables**: []  
**Files Touched**: `backend/tests/integration/test_interactive_replay.py`  
**Roles Ref**: Candidate  
**QA Candidate**: Yes — Observable: End-to-end interactive browser takeover, resume automation, and job replay timeline audit; Mechanism: Pytest integration test; Authz & preconditions: Full stack test setup; Edge & idempotency: Pause, takeover, resume, and timeline verification; Regression: Full platform pipeline.

---

## 👤 User Reference

### Description
Create an end-to-end integration test verifying the interactive browser takeover handshake, automation resumption, and step-by-step job replay timeline generation.

### Acceptance Criteria
- Pytest script runs full submission pipeline.
- Triggers a "Take Control" takeover request, verifies worker pause state, simulates manual completion, and triggers "Resume Automation".
- Asserts worker resumes execution to completion.
- Verifies `/api/v1/applications/{id}/timeline` returns all recorded audit steps in chronological order.

---

## 🤖 AI Agent Reference

### Context Files to Read
- `docs/architecture/design/00-system-architecture-greenfield.md`
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

### QA-Observable Behaviour
- `test_interactive_replay.py` passes 100% of assertions for interactive takeover and timeline audit generation.

### Prerequisites
- Story 10.1, Story 10.2, and Story 9.4 completed.

### Implementation Steps

1. **Create Integration Test (`backend/tests/integration/test_interactive_replay.py`)**:
   - Run submission workflow.
   - Request takeover, assert pause state, resume automation.
   - Fetch timeline endpoint and assert audit steps match chronological order.

### Test Requirements
- Run `pytest backend/tests/integration/test_interactive_replay.py` and verify pass.

### Completion Evidence
- Pytest console output showing clean pass.
