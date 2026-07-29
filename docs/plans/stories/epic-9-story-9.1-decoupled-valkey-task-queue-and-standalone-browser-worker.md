# Story 9.1: Decoupled Valkey Task Queue & Standalone Browser Worker

**BUILDID**: NO-CYCLE | **Epic**: 9 - STANDALONE BROWSER WORKER & EVENT-BASED AUTOMATION | **ID**: 9.1 | **Date**: 2026-07-29 | **Jira**: LOCAL  
**Wave**: 16 | **Requires**: [5.1, 8.1] | **Enables**: [9.2, 9.4]  
**Files Touched**: `backend/app/infrastructure/queue/valkey_queue.py`, `workers/browser_worker.py`  
**Roles Ref**: Candidate  
**QA Candidate**: Yes — Observable: Asynchronous background worker task processing via Valkey; Mechanism: Valkey queue producer/consumer; Authz & preconditions: Valkey credentials; Edge & idempotency: Worker crash isolation and task retries; Regression: Playwright form automation.

---

## 👤 User Reference

### Description
Decouple browser execution into a **Standalone Browser Worker** daemon backed by Valkey message queues. The FastAPI backend never controls Playwright directly; instead, it dispatches application tasks to Valkey (`FastAPI → Queue (Valkey) → Browser Worker → Playwright`). This isolates browser crashes, enables independent worker scaling, and prevents long-running submissions from blocking the web server.

### Acceptance Criteria
- FastAPI backend dispatches application automation tasks asynchronously to Valkey queue.
- Standalone worker daemon (`workers/browser_worker.py`) consumes task payloads from Valkey.
- Worker executes Playwright browser automation in an isolated process.
- Browser crashes or timeouts do not impact FastAPI web server health.

---

## 🤖 AI Agent Reference

### Context Files to Read
- `docs/architecture/design/00-system-architecture-greenfield.md`
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

### QA-Observable Behaviour
- Application task submitted to Valkey queue is processed asynchronously by `workers/browser_worker.py` and updates application status in database.

### Prerequisites
- Story 5.1 and Story 8.1 completed.

### Implementation Steps

1. **Implement Queue Producer/Consumer (`backend/app/infrastructure/queue/valkey_queue.py`)**:
   - Create `ValkeyQueue` helper using `redis-py` / Valkey client for `push_task` and `pop_task`.

2. **Implement Standalone Worker (`workers/browser_worker.py`)**:
   - Long-running worker process polling Valkey queue.
   - Executes `playwright_browser_core.fill_application_form` upon receiving a job application task payload.

### Test Requirements
- Unit tests verifying Valkey queue push/pop and worker task execution.

### Completion Evidence
- Pytest suite passing.
