# Story 9.3: Worker Control UI & Live Telemetry Panel

**BUILDID**: NO-CYCLE | **Epic**: 9 - STANDALONE BROWSER WORKER & EVENT-BASED AUTOMATION | **ID**: 9.3 | **Date**: 2026-07-29 | **Jira**: LOCAL  
**Wave**: 17 | **Requires**: [9.2] | **Enables**: [10.2]  
**Files Touched**: `frontend/src/features/workers/WorkerControlPanel.tsx`, `frontend/src/App.tsx`  
**Roles Ref**: Candidate  
**QA Candidate**: Yes — Observable: Live worker status cards and control buttons; Mechanism: React TSX component; Authz & preconditions: Authenticated Candidate JWT; Edge & idempotency: Pause, Take Control, Stop controls; Regression: Applications dashboard.

---

## 👤 User Reference

### Description
Build a **Live Worker Control UI** giving candidates real-time visibility and control over running automation workers (`Worker #1 - Applying to Microsoft - Current Step: Uploading Resume - Status: Running`). Provides live action buttons: `Pause`, `Take Control`, and `Stop`.

### Acceptance Criteria
- Displays active worker cards with worker ID, target company, current step, and running status.
- Action buttons: `Pause`, `Take Control`, and `Stop`.
- Listens to automation events or polls worker telemetry endpoint for live UI updates.

---

## 🤖 AI Agent Reference

### Context Files to Read
- `docs/architecture/design/00-system-architecture-greenfield.md`
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

### QA-Observable Behaviour
- Candidate can view active worker telemetry and click `Pause` or `Stop` to modify worker execution.

### Prerequisites
- Story 9.2 completed.

### Implementation Steps

1. **Create WorkerControlPanel Component (`frontend/src/features/workers/WorkerControlPanel.tsx`)**:
   - Render worker cards with live status indicators, current step name, and control buttons.

2. **Integrate into Applications Section (`frontend/src/App.tsx`)**:
   - Embed worker control panel in the Applications view.

### Test Requirements
- Frontend build `npm run build` and lint `npm run lint` pass.

### Completion Evidence
- Clean Vite build and ESLint validation.
