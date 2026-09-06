"""
Event dataclasses and EventBus for the automation lifecycle.

Provides a lightweight pub/sub mechanism so that browser worker steps
(task started, worker assigned, form submitted, etc.) can be observed
by any number of async handlers without tight coupling.
"""
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Event dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ApplicationStarted:
    """Emitted when a browser-automation task begins for an application."""

    application_id: str
    job_url: str
    mode: str
    event_type: str = field(default="ApplicationStarted")
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkerAssigned:
    """Emitted when a worker process picks up an application task."""

    application_id: str
    worker_id: str
    event_type: str = field(default="WorkerAssigned")
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SessionValidated:
    """Emitted after the portal session has been checked for validity."""

    application_id: str
    portal_name: str
    is_valid: bool
    event_type: str = field(default="SessionValidated")
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ResumeGenerated:
    """Emitted when a tailored resume artifact has been produced."""

    application_id: str
    resume_path: str
    event_type: str = field(default="ResumeGenerated")
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ApplicationSubmitted:
    """Emitted after the browser worker attempts to submit the application form."""

    application_id: str
    ats_type: str
    submitted: bool
    event_type: str = field(default="ApplicationSubmitted")
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class StatusSaved:
    """Emitted when the application status has been persisted."""

    application_id: str
    status: str
    event_type: str = field(default="StatusSaved")
    timestamp: datetime = field(default_factory=datetime.utcnow)


# Union type alias for all automation events.
AutomationEvent = (
    ApplicationStarted
    | WorkerAssigned
    | SessionValidated
    | ResumeGenerated
    | ApplicationSubmitted
    | StatusSaved
)


# ---------------------------------------------------------------------------
# EventBus
# ---------------------------------------------------------------------------


class EventBus:
    """
    Lightweight async pub/sub event bus for automation lifecycle events.

    Handlers are registered per ``event_type`` string and are called in
    subscription order when an event is emitted.  A failing handler is
    logged and skipped so that it cannot prevent other handlers from
    running.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable]] = {}

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[AutomationEvent], Awaitable[None]],
    ) -> None:
        """
        Register *handler* to be called whenever an event of *event_type* is emitted.

        Args:
            event_type: The string identifier of the event (e.g. ``"ApplicationStarted"``).
            handler:    An async callable that accepts a single ``AutomationEvent`` argument.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    async def emit(self, event: AutomationEvent) -> None:
        """
        Emit *event* to all subscribers registered for its ``event_type``.

        Each handler is awaited in turn.  If a handler raises an exception
        the error is logged and the remaining handlers are still called.

        Args:
            event: The automation event to broadcast.
        """
        event_type: str = event.event_type  # type: ignore[union-attr]
        application_id: str = event.application_id  # type: ignore[union-attr]
        handlers = self._subscribers.get(event_type, [])

        logger.info(
            "event_emitted",
            extra={
                "event_type": event_type,
                "application_id": application_id,
                "subscriber_count": len(handlers),
            },
        )

        for handler in handlers:
            try:
                await handler(event)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "event_handler_error",
                    extra={
                        "event_type": event_type,
                        "application_id": application_id,
                        "handler": getattr(handler, "__name__", repr(handler)),
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                    },
                )

    def subscriber_count(self, event_type: str) -> int:
        """
        Return the number of handlers registered for *event_type*.

        Args:
            event_type: The event type string to query.

        Returns:
            Number of registered handlers, or ``0`` if none.
        """
        return len(self._subscribers.get(event_type, []))


# Module-level singleton — import and use directly.
event_bus = EventBus()
