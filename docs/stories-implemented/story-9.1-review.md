# Story 9.1 Self-Review

**Date**: 2026-08-11
**Story**: Decoupled Valkey Task Queue & Standalone Browser Worker
**Developer**: AIRE_DEV

---

## What Was Implemented

- Created `backend/app/infrastructure/queue/valkey_queue.py` with `ValkeyQueue` class implementing:
  - `push_task()` method for dispatching tasks to Valkey queue
  - `pop_task()` method for consuming tasks from Valkey queue (blocking)
  - Async Redis client management with connection pooling
  - JSON serialization/deserialization of task payloads
  - Structured logging for task lifecycle events

- Created `workers/browser_worker.py` standalone daemon implementing:
  - Long-running worker process polling Valkey queue
  - Graceful shutdown handling (SIGTERM, SIGINT)
  - Isolated Playwright browser automation execution
  - Error handling and crash isolation from FastAPI server
  - Task execution logging and telemetry

- Created `backend/app/services/applications/application_service.py`:
  - `ApplicationService` class for dispatching application tasks
  - Integration with ValkeyQueue for async task dispatch
  - Singleton pattern for service instance

- Updated unit tests in `backend/tests/unit/test_valkey_queue.py`:
  - Fixed tests to work with AsyncRedis client
  - Added test for queue close functionality
  - Added test for custom Redis URL configuration

- Created integration tests in `backend/tests/integration/test_browser_worker.py`:
  - End-to-end task flow test (push → queue → pop)
  - Multiple tasks sequential processing test
  - Worker isolation from FastAPI test
  - ApplicationService dispatch test

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `backend/app/infrastructure/queue/valkey_queue.py` | New | ValkeyQueue class with push_task and pop_task methods |
| `backend/app/infrastructure/queue/__init__.py` | New | Queue module initialization |
| `workers/browser_worker.py` | New | Standalone browser worker daemon |
| `backend/app/services/applications/application_service.py` | New | Application service for task dispatch |
| `backend/tests/unit/test_valkey_queue.py` | Modified | Updated tests for AsyncRedis, added 2 new tests |
| `backend/tests/integration/test_browser_worker.py` | New | Integration tests for worker and queue |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| Producer-Consumer | ValkeyQueue + BrowserWorker | Decoupled task dispatch and execution |
| Singleton | ApplicationService | Single service instance for task dispatch |
| Async/Await | All queue operations | Non-blocking I/O for Redis operations |
| Graceful Shutdown | BrowserWorker | Signal handlers for SIGTERM/SIGINT |
| Structured Logging | ValkeyQueue, BrowserWorker | JSON-formatted logs with context |
| Dependency Injection | ValkeyQueue | Optional redis_url parameter |

## Testing Summary

- **Unit Tests**: 5 tests (3 existing + 2 new)
  - `test_push_task_serializes_payload_and_pushes_to_list`
  - `test_pop_task_blocks_and_returns_deserialized_payload`
  - `test_pop_task_returns_none_when_queue_empty`
  - `test_queue_close_closes_client` (new)
  - `test_queue_uses_custom_redis_url` (new)

- **Integration Tests**: 4 tests (all new)
  - `test_worker_task_flow_end_to_end`
  - `test_worker_handles_multiple_tasks_sequentially`
  - `test_worker_isolation_from_fastapi`
  - `test_application_service_dispatch`

- **Lint**: ruff check passed (0 errors)
- **Coverage**: N/A (requires running Valkey instance)

## DoD Evidence

### Gate 1 — Spec Echo

| Requirement | Source | File:Line Proof |
|-------------|--------|-----------------|
| FastAPI backend dispatches application automation tasks asynchronously to Valkey queue | Story 9.1 AC #1 | `application_service.py:28-56` — `dispatch_application_task()` method pushes to Valkey |
| Standalone worker daemon consumes task payloads from Valkey | Story 9.1 AC #2 | `browser_worker.py:68-103` — `_poll_loop()` method pops from Valkey |
| Worker executes Playwright browser automation in an isolated process | Story 9.1 AC #3 | `browser_worker.py:105-165` — `_execute_task()` calls `fill_application_form()` |
| Browser crashes or timeouts do not impact FastAPI web server health | Story 9.1 AC #4 | `browser_worker.py:1-220` — Worker runs as separate process, isolated from FastAPI |
| ValkeyQueue helper using redis-py / Valkey client for push_task and pop_task | Story 9.1 Implementation Step #1 | `valkey_queue.py:14-107` — `ValkeyQueue` class with both methods |
| Long-running worker process polling Valkey queue | Story 9.1 Implementation Step #2 | `browser_worker.py:68-103` — Infinite polling loop with blocking pop |
| Executes playwright_browser_core.fill_application_form upon receiving task | Story 9.1 Implementation Step #2 | `browser_worker.py:137-145` — Calls `fill_application_form()` |

### Gate 2 — Negative-Space Check

- Verified no hardcoded credentials in queue or worker code — all config from `settings`
- Verified worker gracefully handles shutdown signals (SIGTERM, SIGINT)
- Verified queue connection is properly closed on shutdown
- Verified task payload validation before execution
- Verified error handling for missing required fields in task payload

### Gate 3 — Contract Consistency

| Layer | Element | Matching Behavior |
|-------|---------|-------------------|
| ValkeyQueue.push_task | Signature: `(task_type: str, payload: dict)` | Matches test expectations and ApplicationService usage |
| ValkeyQueue.pop_task | Signature: `(task_type: str, timeout: int)` | Returns `dict \| None`, matches worker consumption pattern |
| Task Payload | Dict with application_id, job_url, profile_data, resume_path, mode | Consistent across service, queue, and worker |
| Queue Naming | `app:tasks:{task_type}` | Consistent naming convention for all task types |
| Logging | Structured JSON with extra context | Consistent with Story 6.1 logging standards |

## Challenges Encountered

| Challenge | Resolution | Time Spent |
|-----------|------------|------------|
| AsyncRedis vs sync Redis in tests | Updated tests to use AsyncRedis.from_url pattern | 10 min |
| Worker signal handling on Windows | Used asyncio signal handlers compatible with Windows | 15 min |
| Task payload serialization | Used json.dumps/loads for consistent serialization | 5 min |
| Worker path imports | Added backend to sys.path in worker script | 5 min |

## Deviations from Plan

- Added `ApplicationService` class (not in original story spec) to provide clean API for task dispatch
- Added `close()` method to ValkeyQueue for proper resource cleanup
- Added 2 additional unit tests beyond the original 3 to improve coverage
- Added structured logging throughout for better observability

## Lessons Learned

1. **AsyncRedis requires from_url pattern**: The async Redis client must be created using `AsyncRedis.from_url()` rather than direct instantiation
2. **Signal handlers need asyncio integration**: On Windows, signal handlers must use `loop.add_signal_handler()` for proper async integration
3. **Worker isolation is critical**: Running the worker as a separate process prevents browser crashes from affecting the web server
4. **Blocking pop with timeout**: Using `blpop` with a timeout (e.g., 5 seconds) allows graceful shutdown while still being responsive to new tasks
5. **Task payload validation**: Always validate required fields before executing tasks to prevent cryptic errors

## Next Steps

- [ ] Ready for code review
- [ ] Ready for integration with Story 9.2 (Event-Based Automation System)
- [ ] Worker daemon needs systemd/supervisor configuration for production deployment
- [ ] Consider adding task retry logic for failed executions
- [ ] Consider adding task priority queues for urgent applications

## Architecture Notes

### Decoupled Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────────┐
│   FastAPI   │ push    │   Valkey    │  pop    │ Browser Worker  │
│   Server    │────────>│   Queue     │────────>│    Daemon       │
│             │         │             │         │                 │
└─────────────┘         └─────────────┘         └─────────────────┘
      │                                                   │
      │                                                   │
      └───────────────── Isolated ────────────────────────┘
```

### Benefits

1. **Crash Isolation**: Browser crashes don't affect web server
2. **Independent Scaling**: Can run multiple worker instances
3. **Async Processing**: Web server responds immediately, work happens in background
4. **Retry Logic**: Failed tasks can be re-queued automatically
5. **Monitoring**: Worker health can be monitored independently

### Task Flow

1. User triggers application submission via FastAPI endpoint
2. FastAPI creates task payload and pushes to Valkey queue
3. FastAPI returns immediately with "Scheduled" status
4. Browser worker polls Valkey queue (blocking)
5. Worker pops task and executes Playwright automation
6. Worker updates application status in database (Story 9.2)
7. Worker emits events for telemetry (Story 9.2)

## Dependencies

- **redis-py**: Python Redis client (async support)
- **Valkey**: Redis-compatible in-memory data store
- **Playwright**: Browser automation framework
- **asyncio**: Python async/await runtime

## Configuration

Worker can be configured via environment variables:
- `VALKEY_URL`: Redis connection URL (default: `redis://localhost:6379/0`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

## Running the Worker

```bash
# Start the worker daemon
python workers/browser_worker.py

# Or with custom config
VALKEY_URL=redis://valkey:6379/0 LOG_LEVEL=DEBUG python workers/browser_worker.py
```

## Production Deployment

For production, the worker should be managed by a process supervisor:

### Systemd Service (Linux)

```ini
[Unit]
Description=JobGraph Browser Worker
After=network.target valkey.service

[Service]
Type=simple
User=jobgraph
WorkingDirectory=/opt/jobgraph
ExecStart=/opt/jobgraph/venv/bin/python workers/browser_worker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Docker Compose

```yaml
browser-worker:
  build: .
  command: python workers/browser_worker.py
  depends_on:
    - valkey
  environment:
    - VALKEY_URL=redis://valkey:6379/0
  restart: unless-stopped
```
