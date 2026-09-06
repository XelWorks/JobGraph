"""
Integration tests for Worker Queue and EventBus.

Tests cover:
- ValkeyQueue push/pop payload integrity
- BrowserWorker._execute_task event emissions (WorkerAssigned, ApplicationStarted,
  ApplicationSubmitted, StatusSaved)
- Invalid payload handling
- EventBus multi-subscriber and isolation behaviour

All tests are fully self-contained — no real Valkey or database required.
"""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.queue.valkey_queue import ValkeyQueue
from app.services.automation.events import (
    ApplicationStarted,
    EventBus,
    StatusSaved,
    WorkerAssigned,
)

# ---------------------------------------------------------------------------
# Add workers/ directory to sys.path so BrowserWorker can be imported
# ---------------------------------------------------------------------------
workers_path = Path(__file__).resolve().parents[3] / "workers"
sys.path.insert(0, str(workers_path))
from browser_worker import BrowserWorker  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_TASK: dict = {
    "application_id": "app-42",
    "job_url": "https://jobs.example.com/apply/123",
    "profile_data": {"name": "Jane Doe", "email": "jane@example.com"},
    "resume_path": "/tmp/resume.pdf",
    "mode": "Autonomous",
}

FILL_FORM_SUCCESS = {
    "status": "success",
    "ats_type": "greenhouse",
    "submitted": True,
}

FILL_FORM_AUTO_FILLED = {
    "status": "success",
    "ats_type": "workday",
    "submitted": False,
}


# ===========================================================================
# Group 1 — Queue + Worker task flow
# ===========================================================================


@pytest.mark.asyncio
async def test_task_pushed_to_queue_and_popped_by_worker() -> None:
    """
    Push a task via ValkeyQueue.push_task, mock the AsyncRedis client,
    pop it back, and assert payload integrity.
    """
    # Arrange
    queue = ValkeyQueue(redis_url="redis://localhost:6379")
    mock_client = AsyncMock()

    # rpush succeeds silently
    mock_client.rpush = AsyncMock(return_value=1)

    # blpop returns (queue_name, serialized_payload)
    import json

    serialized = json.dumps(SAMPLE_TASK)
    mock_client.blpop = AsyncMock(return_value=("app:tasks:application", serialized))

    queue._client = mock_client

    # Act
    await queue.push_task("application", SAMPLE_TASK)
    result = await queue.pop_task("application", timeout=1)

    # Assert
    assert result is not None
    assert result["application_id"] == SAMPLE_TASK["application_id"]
    assert result["job_url"] == SAMPLE_TASK["job_url"]
    assert result["profile_data"] == SAMPLE_TASK["profile_data"]
    assert result["resume_path"] == SAMPLE_TASK["resume_path"]
    assert result["mode"] == SAMPLE_TASK["mode"]


@pytest.mark.asyncio
async def test_worker_execute_task_emits_worker_assigned_event() -> None:
    """
    BrowserWorker._execute_task should emit a WorkerAssigned event.
    """
    # Arrange
    fresh_bus = EventBus()
    handler = AsyncMock()
    fresh_bus.subscribe("WorkerAssigned", handler)

    worker = BrowserWorker()

    with (
        patch("browser_worker.event_bus", fresh_bus),
        patch.object(
            worker.browser_core,
            "fill_application_form",
            new=AsyncMock(return_value=FILL_FORM_SUCCESS),
        ),
    ):
        # Act
        await worker._execute_task(SAMPLE_TASK)

    # Assert
    handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_worker_execute_task_emits_application_started_event() -> None:
    """
    BrowserWorker._execute_task should emit ApplicationStarted with the correct job_url.
    """
    # Arrange
    fresh_bus = EventBus()
    handler = AsyncMock()
    fresh_bus.subscribe("ApplicationStarted", handler)

    worker = BrowserWorker()

    with (
        patch("browser_worker.event_bus", fresh_bus),
        patch.object(
            worker.browser_core,
            "fill_application_form",
            new=AsyncMock(return_value=FILL_FORM_SUCCESS),
        ),
    ):
        # Act
        await worker._execute_task(SAMPLE_TASK)

    # Assert
    handler.assert_awaited_once()
    emitted_event: ApplicationStarted = handler.call_args[0][0]
    assert emitted_event.job_url == SAMPLE_TASK["job_url"]


@pytest.mark.asyncio
async def test_worker_execute_task_emits_application_submitted_event() -> None:
    """
    BrowserWorker._execute_task should emit ApplicationSubmitted with
    submitted=True and ats_type='greenhouse'.
    """
    # Arrange
    fresh_bus = EventBus()
    handler = AsyncMock()
    fresh_bus.subscribe("ApplicationSubmitted", handler)

    worker = BrowserWorker()

    with (
        patch("browser_worker.event_bus", fresh_bus),
        patch.object(
            worker.browser_core,
            "fill_application_form",
            new=AsyncMock(return_value=FILL_FORM_SUCCESS),
        ),
    ):
        # Act
        await worker._execute_task(SAMPLE_TASK)

    # Assert
    handler.assert_awaited_once()
    emitted_event = handler.call_args[0][0]
    assert emitted_event.submitted is True
    assert emitted_event.ats_type == "greenhouse"


@pytest.mark.asyncio
async def test_worker_execute_task_emits_status_saved_submitted() -> None:
    """
    When fill_application_form returns submitted=True, StatusSaved should
    carry status='Submitted'.
    """
    # Arrange
    fresh_bus = EventBus()
    handler = AsyncMock()
    fresh_bus.subscribe("StatusSaved", handler)

    worker = BrowserWorker()

    with (
        patch("browser_worker.event_bus", fresh_bus),
        patch.object(
            worker.browser_core,
            "fill_application_form",
            new=AsyncMock(return_value=FILL_FORM_SUCCESS),
        ),
    ):
        # Act
        await worker._execute_task(SAMPLE_TASK)

    # Assert
    handler.assert_awaited_once()
    emitted_event: StatusSaved = handler.call_args[0][0]
    assert emitted_event.status == "Submitted"


@pytest.mark.asyncio
async def test_worker_execute_task_emits_status_saved_auto_filled() -> None:
    """
    When fill_application_form returns submitted=False, StatusSaved should
    carry status='Auto-Filled'.
    """
    # Arrange
    fresh_bus = EventBus()
    handler = AsyncMock()
    fresh_bus.subscribe("StatusSaved", handler)

    worker = BrowserWorker()

    with (
        patch("browser_worker.event_bus", fresh_bus),
        patch.object(
            worker.browser_core,
            "fill_application_form",
            new=AsyncMock(return_value=FILL_FORM_AUTO_FILLED),
        ),
    ):
        # Act
        await worker._execute_task(SAMPLE_TASK)

    # Assert
    handler.assert_awaited_once()
    emitted_event: StatusSaved = handler.call_args[0][0]
    assert emitted_event.status == "Auto-Filled"


@pytest.mark.asyncio
async def test_worker_execute_task_marks_review_required_browser_result_as_scheduled() -> None:
    """
    A browser result that triggers manual review should be persisted as Scheduled,
    even when the task was not pre-marked with requires_review.
    """
    # Arrange
    fresh_bus = EventBus()
    handler = AsyncMock()
    fresh_bus.subscribe("StatusSaved", handler)

    worker = BrowserWorker()
    review_result = {
        "status": "review_required",
        "ats_type": "linkedin",
        "requires_manual_review": True,
        "submitted": False,
    }

    with (
        patch("browser_worker.event_bus", fresh_bus),
        patch.object(
            worker.browser_core,
            "fill_application_form",
            new=AsyncMock(return_value=review_result),
        ),
    ):
        # Act
        await worker._execute_task(SAMPLE_TASK)

    # Assert
    handler.assert_awaited_once()
    emitted_event: StatusSaved = handler.call_args[0][0]
    assert emitted_event.status == "Scheduled"


@pytest.mark.asyncio
async def test_worker_execute_task_emits_status_saved_failed_on_exception() -> None:
    """
    When fill_application_form raises an exception, StatusSaved should
    carry status='Failed'.
    """
    # Arrange
    fresh_bus = EventBus()
    handler = AsyncMock()
    fresh_bus.subscribe("StatusSaved", handler)

    worker = BrowserWorker()

    with (
        patch("browser_worker.event_bus", fresh_bus),
        patch.object(
            worker.browser_core,
            "fill_application_form",
            new=AsyncMock(side_effect=RuntimeError("browser crash")),
        ),
    ):
        # Act
        await worker._execute_task(SAMPLE_TASK)

    # Assert
    handler.assert_awaited_once()
    emitted_event: StatusSaved = handler.call_args[0][0]
    assert emitted_event.status == "Failed"


@pytest.mark.asyncio
async def test_worker_execute_task_skips_invalid_payload() -> None:
    """
    When the task payload is missing job_url and resume_path,
    fill_application_form must NOT be called.
    """
    # Arrange
    worker = BrowserWorker()
    mock_fill = AsyncMock(return_value=FILL_FORM_SUCCESS)

    invalid_task: dict = {
        "application_id": "app-99",
        "profile_data": {"name": "Ghost"},
        "mode": "Autonomous",
        # job_url and resume_path intentionally omitted
    }

    with patch.object(worker.browser_core, "fill_application_form", new=mock_fill):
        # Act
        await worker._execute_task(invalid_task)

    # Assert
    mock_fill.assert_not_awaited()


# ===========================================================================
# Group 2 — EventBus integration
# ===========================================================================


@pytest.mark.asyncio
async def test_event_bus_multiple_subscribers_all_called() -> None:
    """
    All 3 subscribers registered for the same event type must be called
    when that event is emitted.
    """
    # Arrange
    bus = EventBus()
    handler_a = AsyncMock()
    handler_b = AsyncMock()
    handler_c = AsyncMock()

    bus.subscribe("ApplicationStarted", handler_a)
    bus.subscribe("ApplicationStarted", handler_b)
    bus.subscribe("ApplicationStarted", handler_c)

    event = ApplicationStarted(
        application_id="app-1",
        job_url="https://jobs.example.com/1",
        mode="Autonomous",
    )

    # Act
    await bus.emit(event)

    # Assert
    handler_a.assert_awaited_once()
    handler_b.assert_awaited_once()
    handler_c.assert_awaited_once()


@pytest.mark.asyncio
async def test_event_bus_subscriber_isolation_across_event_types() -> None:
    """
    A handler subscribed to WorkerAssigned must NOT be called when a
    StatusSaved event is emitted, and vice versa.
    """
    # Arrange
    bus = EventBus()
    handler_a = AsyncMock()
    handler_b = AsyncMock()

    bus.subscribe("WorkerAssigned", handler_a)
    bus.subscribe("StatusSaved", handler_b)

    worker_assigned_event = WorkerAssigned(
        application_id="app-2",
        worker_id="pid-1234",
    )

    # Act
    await bus.emit(worker_assigned_event)

    # Assert
    handler_a.assert_awaited_once()
    handler_b.assert_not_awaited()
