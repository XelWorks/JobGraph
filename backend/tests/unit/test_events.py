"""
Unit tests for the automation EventBus and event dataclasses.

Tests follow the Arrange-Act-Assert (AAA) pattern and use AsyncMock for
async handler verification.
"""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.services.automation.events import (
    ApplicationStarted,
    ApplicationSubmitted,
    EventBus,
    ResumeGenerated,
    SessionValidated,
    StatusSaved,
    WorkerAssigned,
)


# ---------------------------------------------------------------------------
# EventBus behaviour tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_event_bus_subscribe_and_emit() -> None:
    """A subscribed handler is called exactly once when a matching event is emitted."""
    # Arrange
    bus = EventBus()
    handler = AsyncMock()
    event = ApplicationStarted(
        application_id="app-1",
        job_url="https://example.com/job/1",
        mode="Autonomous",
    )
    bus.subscribe("ApplicationStarted", handler)

    # Act
    await bus.emit(event)

    # Assert
    handler.assert_awaited_once_with(event)


@pytest.mark.asyncio
async def test_event_bus_emit_calls_all_subscribers() -> None:
    """All handlers subscribed to the same event_type are called when the event is emitted."""
    # Arrange
    bus = EventBus()
    handler_a = AsyncMock()
    handler_b = AsyncMock()
    event = ApplicationStarted(
        application_id="app-2",
        job_url="https://example.com/job/2",
        mode="Assisted",
    )
    bus.subscribe("ApplicationStarted", handler_a)
    bus.subscribe("ApplicationStarted", handler_b)

    # Act
    await bus.emit(event)

    # Assert
    handler_a.assert_awaited_once_with(event)
    handler_b.assert_awaited_once_with(event)


@pytest.mark.asyncio
async def test_event_bus_emit_different_event_types_only_calls_matching_subscribers() -> None:
    """Emitting event type X does not invoke handlers registered for event type Y."""
    # Arrange
    bus = EventBus()
    handler_a = AsyncMock()
    handler_b = AsyncMock()
    event = ApplicationStarted(
        application_id="app-3",
        job_url="https://example.com/job/3",
        mode="Manual",
    )
    bus.subscribe("ApplicationStarted", handler_a)
    bus.subscribe("StatusSaved", handler_b)

    # Act
    await bus.emit(event)

    # Assert
    handler_a.assert_awaited_once_with(event)
    handler_b.assert_not_awaited()


@pytest.mark.asyncio
async def test_event_bus_subscriber_count() -> None:
    """subscriber_count returns the correct count for registered and unregistered types."""
    # Arrange
    bus = EventBus()
    bus.subscribe("ApplicationStarted", AsyncMock())
    bus.subscribe("ApplicationStarted", AsyncMock())

    # Act & Assert
    assert bus.subscriber_count("ApplicationStarted") == 2
    assert bus.subscriber_count("StatusSaved") == 0


@pytest.mark.asyncio
async def test_event_bus_bad_handler_does_not_stop_other_handlers() -> None:
    """A handler that raises an exception must not prevent subsequent handlers from running."""
    # Arrange
    bus = EventBus()

    async def bad_handler(event: ApplicationStarted) -> None:  # noqa: ARG001
        raise RuntimeError("handler exploded")

    good_handler = AsyncMock()
    event = ApplicationStarted(
        application_id="app-4",
        job_url="https://example.com/job/4",
        mode="Autonomous",
    )
    bus.subscribe("ApplicationStarted", bad_handler)
    bus.subscribe("ApplicationStarted", good_handler)

    # Act — must not raise
    await bus.emit(event)

    # Assert
    good_handler.assert_awaited_once_with(event)


@pytest.mark.asyncio
async def test_event_bus_emit_no_subscribers_does_not_raise() -> None:
    """Emitting an event when no handlers are registered must not raise any exception."""
    # Arrange
    bus = EventBus()
    event = StatusSaved(application_id="app-5", status="Submitted")

    # Act & Assert — no exception expected
    await bus.emit(event)


# ---------------------------------------------------------------------------
# Event dataclass field tests
# ---------------------------------------------------------------------------


def test_application_started_event_fields() -> None:
    """ApplicationStarted carries the correct event_type and all required fields."""
    # Arrange & Act
    event = ApplicationStarted(
        application_id="app-1",
        job_url="https://example.com",
        mode="Autonomous",
    )

    # Assert
    assert event.event_type == "ApplicationStarted"
    assert event.application_id == "app-1"
    assert event.job_url == "https://example.com"
    assert event.mode == "Autonomous"
    assert isinstance(event.timestamp, datetime)


def test_worker_assigned_event_fields() -> None:
    """WorkerAssigned carries the correct event_type and all required fields."""
    # Arrange & Act
    event = WorkerAssigned(application_id="app-10", worker_id="12345")

    # Assert
    assert event.event_type == "WorkerAssigned"
    assert event.application_id == "app-10"
    assert event.worker_id == "12345"
    assert isinstance(event.timestamp, datetime)


def test_session_validated_event_fields() -> None:
    """SessionValidated carries the correct event_type and all required fields."""
    # Arrange & Act
    event = SessionValidated(
        application_id="app-20",
        portal_name="LinkedIn",
        is_valid=True,
    )

    # Assert
    assert event.event_type == "SessionValidated"
    assert event.application_id == "app-20"
    assert event.portal_name == "LinkedIn"
    assert event.is_valid is True
    assert isinstance(event.timestamp, datetime)


def test_resume_generated_event_fields() -> None:
    """ResumeGenerated carries the correct event_type and all required fields."""
    # Arrange & Act
    event = ResumeGenerated(
        application_id="app-30",
        resume_path="/tmp/resume_app30.pdf",
    )

    # Assert
    assert event.event_type == "ResumeGenerated"
    assert event.application_id == "app-30"
    assert event.resume_path == "/tmp/resume_app30.pdf"
    assert isinstance(event.timestamp, datetime)


def test_application_submitted_event_fields() -> None:
    """ApplicationSubmitted carries the correct event_type and all required fields."""
    # Arrange & Act
    event = ApplicationSubmitted(
        application_id="app-40",
        ats_type="Greenhouse",
        submitted=True,
    )

    # Assert
    assert event.event_type == "ApplicationSubmitted"
    assert event.application_id == "app-40"
    assert event.ats_type == "Greenhouse"
    assert event.submitted is True
    assert isinstance(event.timestamp, datetime)


def test_status_saved_event_fields() -> None:
    """StatusSaved carries the correct event_type and all required fields."""
    # Arrange & Act
    event = StatusSaved(application_id="app-50", status="Submitted")

    # Assert
    assert event.event_type == "StatusSaved"
    assert event.application_id == "app-50"
    assert event.status == "Submitted"
    assert isinstance(event.timestamp, datetime)


@pytest.mark.asyncio
async def test_status_saved_event_persists_application_status() -> None:
    """When a StatusSaved event fires, the application record is updated with the status."""
    from app.services.automation.status_tracker import persist_status_saved_event

    mock_session = AsyncMock()
    application_id = uuid.uuid4()
    with (
        patch("app.services.automation.status_tracker.SessionLocal") as mock_session_factory,
        patch("app.services.automation.status_tracker.application_repository.update_artifacts", AsyncMock()) as mock_update,
    ):
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        event = StatusSaved(application_id=str(application_id), status="Scheduled")

        await persist_status_saved_event(event)

    mock_update.assert_awaited_once_with(mock_session, application_id, status="Scheduled", date_applied=None)
