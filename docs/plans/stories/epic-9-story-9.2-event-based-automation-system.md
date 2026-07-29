# Story 9.2: Event-Based Automation System

**BUILDID**: NO-CYCLE | **Epic**: 9 - STANDALONE BROWSER WORKER & EVENT-BASED AUTOMATION | **ID**: 9.2 | **Date**: 2026-07-29 | **Jira**: LOCAL  
**Wave**: 16 | **Requires**: [9.1] | **Enables**: [9.3, 9.4, 10.1]  
**Files Touched**: `backend/app/services/automation/events.py`  
**Roles Ref**: Candidate  
**QA Candidate**: Yes — Observable: Structured automation lifecycle events; Mechanism: Event bus pub/sub; Authz & preconditions: Internal event context; Edge & idempotency: Out-of-order event handling; Regression: Application status updates.

---

## 👤 User Reference

### Description
Replace continuous polling with an **Event-Based Automation System**. Every application step emits explicit lifecycle events (`ApplicationStarted` → `WorkerAssigned` → `SessionValidated` → `ResumeGenerated` → `ApplicationSubmitted` → `StatusSaved` → `AnalyticsUpdated`). This provides live UI updates, enables automated retries, and records step-by-step audit logs.

### Acceptance Criteria
- Defines structured event schemas for every stage of the automation lifecycle.
- In-memory/Valkey event bus broadcasts lifecycle events to listeners.
- Event listeners update application status, audit logs, and dashboard metrics automatically.

---

## 🤖 AI Agent Reference

### Context Files to Read
- `docs/architecture/design/00-system-architecture-greenfield.md`
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

### QA-Observable Behaviour
- Dispatched events (`ApplicationStarted`, `WorkerAssigned`, `ApplicationSubmitted`) are emitted and handled in sequence.

### Prerequisites
- Story 9.1 completed.

### Implementation Steps

1. **Create Event System (`backend/app/services/automation/events.py`)**:
   - Define event dataclasses: `ApplicationStarted`, `WorkerAssigned`, `SessionValidated`, `ResumeGenerated`, `ApplicationSubmitted`, `StatusSaved`.
   - Implement `EventBus` pub/sub for emitting and subscribing to automation lifecycle events.

### Test Requirements
- Unit tests verifying event emission and subscriber handling.

### Completion Evidence
- Pytest suite passing.
