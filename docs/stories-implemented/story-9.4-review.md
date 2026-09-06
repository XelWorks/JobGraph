# Story 9.4 — Self-Review

**Date**: 2026-08-11
**Story**: Worker Queue Integration Test
**Developer**: AIRE_DEV
**Status**: ✅ Done

---

## What Was Implemented

10 integration tests covering the full worker queue and event system:

**Group 1 — Queue + Worker task flow (8 tests):**

1. `test_task_pushed_to_queue_and_popped_by_worker` — Mocked AsyncRedis client; verifies all payload fields (application_id, job_url, profile_data, resume_path, mode) survive a push/pop round-trip.
2. `test_worker_execute_task_emits_worker_assigned_event` — Asserts `WorkerAssigned` handler is awaited once when `_execute_task` runs successfully.
3. `test_worker_execute_task_emits_application_started_event` — Asserts `ApplicationStarted` handler is called with the correct `job_url`.
4. `test_worker_execute_task_emits_application_submitted_event` — Asserts `ApplicationSubmitted` carries `submitted=True` and `ats_type="greenhouse"`.
5. `test_worker_execute_task_emits_status_saved_submitted` — Asserts `StatusSaved.status == "Submitted"` when `fill_application_form` returns `submitted=True`.
6. `test_worker_execute_task_emits_status_saved_auto_filled` — Asserts `StatusSaved.status == "Auto-Filled"` when `submitted=False`.
7. `test_worker_execute_task_emits_status_saved_failed_on_exception` — Mocks `fill_application_form` to raise `RuntimeError`; asserts `StatusSaved.status == "Failed"`.
8. `test_worker_execute_task_skips_invalid_payload` — Payload missing `job_url` and `resume_path`; asserts `fill_application_form` is NOT called.

**Group 2 — EventBus integration (2 tests):**

9. `test_event_bus_multiple_subscribers_all_called` — 3 handlers subscribed to `"ApplicationStarted"`; all 3 awaited after a single emit.
10. `test_event_bus_subscriber_isolation_across_event_types` — `handler_a` on `"WorkerAssigned"`, `handler_b` on `"StatusSaved"`; only `handler_a` called when `WorkerAssigned` is emitted.

---

## Files Changed

| File | Change |
|------|--------|
| `backend/tests/integration/test_worker_queue.py` | New — 10 integration tests |

---

## Patterns Applied

- **AAA** (Arrange / Act / Assert) structure throughout.
- `pytest-asyncio` with `@pytest.mark.asyncio` decorator on every test.
- `AsyncMock` for async handlers and `fill_application_form`.
- `patch("browser_worker.event_bus", fresh_bus)` to isolate each test's `EventBus` instance from the module-level singleton.
- `patch.object(worker.browser_core, "fill_application_form", ...)` to avoid real Playwright execution.
- Fresh `EventBus` instance per test — no shared mutable state between tests.
- stdlib → third-party → local import ordering.
- Full type hints on all variables and function signatures.

---

## Testing Summary

- 10 tests, all passing.
- No real Valkey, PostgreSQL, or Playwright required.
- `ruff` lint: clean.

---

## DoD Evidence — Gate 1

| Acceptance Criterion | Test(s) |
|----------------------|---------|
| AC1: Queue push/pop preserves full payload | `test_task_pushed_to_queue_and_popped_by_worker` |
| AC2: Worker emits correct lifecycle events | Tests 2–7 (WorkerAssigned, ApplicationStarted, ApplicationSubmitted, StatusSaved) |
| AC3: EventBus correctly routes events to subscribers | Tests 9–10 (multi-subscriber, isolation) |

---

## Next Steps

- Ready for code review.
- Tests can be extended with real Valkey integration once a test container is available in CI.
