# Story 10.2: Job Replay Timeline UI & Audit Log Service

**BUILDID**: NO-CYCLE | **Epic**: 10 - INTERACTIVE CONTROL & JOB REPLAY AUDIT | **ID**: 10.2 | **Date**: 2026-07-29 | **Jira**: LOCAL  
**Wave**: 18 | **Requires**: [9.2, 9.3] | **Enables**: [10.3]  
**Files Touched**: `frontend/src/features/applications/JobReplayTimeline.tsx`, `backend/app/services/automation/audit_log.py`  
**Roles Ref**: Candidate  
**QA Candidate**: Yes — Observable: Step-by-step audit log timeline for submitted applications; Mechanism: Audit log service & React TSX timeline component; Authz & preconditions: Authenticated Candidate JWT; Edge & idempotency: Exact step error highlighting; Regression: Application tracking dashboard.

---

## 👤 User Reference

### Description
Build a **Job Replay Timeline UI** and Audit Log service. Every application stores a step-by-step execution timeline (`09:10 Browser Opened` → `09:10 Logged In` → `09:11 Resume Uploaded` → `09:11 Question Answered` → `09:12 Application Submitted`). If a run fails, the candidate can inspect the replay timeline to see exactly where and why the failure occurred.

### Acceptance Criteria
- Stores step-by-step execution timestamps and event logs for every application run.
- UI renders an interactive timeline displaying steps, timestamps, status badges, and failure messages.
- Exposes API endpoint `/api/v1/applications/{id}/timeline` to fetch audit history.

---

## 🤖 AI Agent Reference

### Context Files to Read
- `docs/architecture/design/00-system-architecture-greenfield.md`
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

### QA-Observable Behaviour
- Candidate can click "View Replay Timeline" on any application tracking entry and inspect the chronological step-by-step audit logs.

### Prerequisites
- Story 9.2 and Story 9.3 completed.

### Implementation Steps

1. **Implement Audit Log Service (`backend/app/services/automation/audit_log.py`)**:
   - Record timestamps, step names, and status for each event in `ApplicationStarted`, `ResumeUploaded`, `QuestionAnswered`, `ApplicationSubmitted`.

2. **Create JobReplayTimeline Component (`frontend/src/features/applications/JobReplayTimeline.tsx`)**:
   - Render vertical timeline with step icons, timestamps, and error highlights.

### Test Requirements
- Frontend build `npm run build` and lint `npm run lint` pass.

### Completion Evidence
- Clean Vite build and ESLint validation.
