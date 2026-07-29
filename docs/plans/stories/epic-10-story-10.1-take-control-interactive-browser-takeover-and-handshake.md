# Story 10.1: 'Take Control' Interactive Browser Takeover & Handshake

**BUILDID**: NO-CYCLE | **Epic**: 10 - INTERACTIVE CONTROL & JOB REPLAY AUDIT | **ID**: 10.1 | **Date**: 2026-07-29 | **Jira**: LOCAL  
**Wave**: 18 | **Requires**: [9.1, 9.2] | **Enables**: [10.3]  
**Files Touched**: `backend/app/services/automation/takeover.py`  
**Roles Ref**: Candidate  
**QA Candidate**: Yes — Observable: Interactive browser takeover protocol for CAPTCHA/MFA; Mechanism: WebSocket / takeover handshake REST endpoint; Authz & preconditions: Active worker task; Edge & idempotency: Pause, manual interaction, and resume automation handshake; Regression: Playwright automation core.

---

## 👤 User Reference

### Description
Implement the **"Take Control"** interactive browser takeover protocol. When automated form submission encounters an unexpected challenge (CAPTCHA, weird form, custom question, MFA), the candidate clicks **Take Control**. The worker pauses, connects the browser session interactively, allows the candidate to complete the step manually, and then resumes automated execution seamlessly when the candidate clicks **Resume Automation**.

### Acceptance Criteria
- Automation worker detects CAPTCHA/MFA or receives a "Take Control" user trigger and pauses.
- Exposes takeover handshake protocol preserving the Playwright page session state.
- Candidate completes manual interaction and clicks "Resume Automation".
- Worker resumes automation execution from the exact step where it paused.

---

## 🤖 AI Agent Reference

### Context Files to Read
- `docs/architecture/design/00-system-architecture-greenfield.md`
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

### QA-Observable Behaviour
- Worker enters `paused_for_takeover` state when takeover is requested, preserves page session, and resumes submission upon `resume_automation` trigger.

### Prerequisites
- Story 9.1 and Story 9.2 completed.

### Implementation Steps

1. **Implement Takeover Service (`backend/app/services/automation/takeover.py`)**:
   - Create `TakeoverManager` to handle `request_takeover()`, `pause_worker()`, and `resume_automation()`.
   - Implement WebSocket / HTTP handshake for interactive session transfers.

### Test Requirements
- Unit tests verifying takeover pause and resume handshake.

### Completion Evidence
- Pytest suite passing.
