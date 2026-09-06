"""Automation services for event-based lifecycle management."""
from app.services.automation.browser_runtime import PortalAutomationRuntime
from app.services.automation.events import EventBus, event_bus
from app.services.automation.status_tracker import (
    persist_application_submitted_event,
    persist_status_saved_event,
)

event_bus.subscribe("StatusSaved", persist_status_saved_event)
event_bus.subscribe("ApplicationSubmitted", persist_application_submitted_event)

__all__ = [
    "EventBus",
    "event_bus",
    "PortalAutomationRuntime",
    "persist_status_saved_event",
    "persist_application_submitted_event",
]
