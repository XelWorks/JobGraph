# Story 8.2: Browser Profile Manager UI & Fingerprint Inspector

**BUILDID**: NO-CYCLE | **Epic**: 8 - BROWSER PROFILE & CONNECTOR SDK | **ID**: 8.2 | **Date**: 2026-07-29 | **Jira**: LOCAL  
**Wave**: 15 | **Requires**: [7.2, 8.1] | **Enables**: []  
**Files Touched**: `frontend/src/features/vault/BrowserProfileManager.tsx`, `frontend/src/App.tsx`  
**Roles Ref**: Candidate  
**QA Candidate**: Yes — Observable: Browser profile inspector card with session health indicators; Mechanism: React TSX dashboard view; Authz & preconditions: Authenticated Candidate JWT; Edge & idempotency: Cookie export/delete actions; Regression: Account Hub navigation.

---

## 👤 User Reference

### Description
Expose browser profile management in the UI. Instead of hiding cookies in background storage, the Browser Profile Manager lets candidates inspect browser profiles (Chromium engine, user-agent fingerprint, session health, cookie validity, local storage presence), open interactive browser contexts, reconnect expired sessions, and export or delete browser profiles.

### Acceptance Criteria
- Displays browser profile cards for connected portals (e.g. "LinkedIn - Desktop Linux Chrome 139").
- Exposes session health badges (`Healthy`, `Cookies Valid`, `Storage Present`).
- Action buttons for `Open Browser`, `Reconnect`, `Export Cookies`, and `Delete Profile`.
- Connects to backend Session Vault and Browser Profile endpoints.

---

## 🤖 AI Agent Reference

### Context Files to Read
- `docs/architecture/design/00-system-architecture-greenfield.md`
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

### RBAC Enforcement
No role-differentiated access — single actor (Candidate).

### QA-Observable Behaviour
- Candidate can view browser profile details (user-agent fingerprint, cookie status, storage presence) and trigger cookie exports or profile deletions.

### Prerequisites
- Story 7.2 and Story 8.1 completed.

### Implementation Steps

1. **Create BrowserProfileManager Component (`frontend/src/features/vault/BrowserProfileManager.tsx`)**:
   - Render browser profile cards displaying profile name, engine, session health, last verified time, cookies status, storage status, and user-agent fingerprint.
   - Add action buttons: `Open Browser`, `Reconnect`, `Export`, `Delete`.

2. **Integrate into Account Hub View (`frontend/src/features/vault/AccountHub.tsx`)**:
   - Embed BrowserProfileManager inside Account Hub as a tabbed or stacked section.

### Test Requirements
- Frontend build `npm run build` and lint `npm run lint` pass with zero errors.

### Completion Evidence
- Clean Vite build and ESLint validation.
