# Story 8.4: LinkedIn, Naukri & Glassdoor Portal Connectors and Safe Auto-Apply Runtime

**BUILDID**: NO-CYCLE | **Epic**: 8 - BROWSER PROFILE & CONNECTOR SDK | **ID**: 8.4 | **Date**: 2026-08-31 | **Jira**: LOCAL  
**Wave**: 15 | **Requires**: [7.1, 8.1, 9.1] | **Enables**: [9.2, 10.1, 10.3]  
**Files Touched**: `backend/app/services/discovery/connector.py`, `backend/app/services/discovery/connector_sdk.py`, `backend/app/infrastructure/browser/playwright_client.py`, `backend/app/services/automation/`, `frontend/src/features/vault/`, `frontend/src/features/workers/`  
**Roles Ref**: Candidate  
**QA Candidate**: Yes — Observable: Real portal connector coverage for LinkedIn, Naukri, and Glassdoor with session-safe automation; Mechanism: connector SDK + browser profile runtime + safety policy checks; Authz & preconditions: Active session vault entries and browser profile setup; Edge & idempotency: CAPTCHA/MFA, retry/backoff, and manual takeover; Regression: Greenhouse/Lever plus new portal coverage.

---

## 👤 User Reference

### Description
Close the major product gap by adding vendor-specific portal connectors and a safe runtime for autonomous job applications across LinkedIn, Naukri, Glassdoor, and company career pages. This work turns the current generic ATS automation foundation into a real-world apply engine with session persistence, platform-aware form handling, safety rules, retry logic, and manual takeover support when a site challenges the browser.

### Acceptance Criteria
- `LinkedInConnector`, `NaukriConnector`, and `GlassdoorConnector` implement the unified `BasePortalConnector` contract.
- Each connector supports `connect`, `disconnect`, `validate_session`, `search_jobs`, `apply`, `health_check`, and `refresh_session`.
- Session vault data is used to restore browser cookies/local storage for each portal before application attempts.
- Playwright automation detects job portals and career pages, then fills the correct fields for each provider.
- The runtime enforces safety gates: allowlist/denylist, rate limits, max attempts, pause/resume controls, and explicit confirmation before risky submits.
- CAPTCHA/MFA or unusual blockers trigger the interactive takeover flow instead of hard-failing the automation.
- The system can apply to company career pages and ATS forms (Greenhouse, Lever, Workday) as part of the same workflow.
- Test coverage includes connector contract tests and one end-to-end mocked portal flow that verifies session restore + apply success signaling.

---

## 🤖 AI Agent Reference

### Context Files to Read
- `docs/requirements.md`
- `docs/architecture/design/00-system-architecture-greenfield.md`
- `docs/plans/stories/epic-8-story-8.1-unified-connector-sdk.md`
- `docs/plans/stories/epic-9-story-9.1-decoupled-valkey-task-queue-and-standalone-browser-worker.md`
- `docs/plans/stories/epic-10-story-10.1-take-control-interactive-browser-takeover-and-handshake.md`

### RBAC Enforcement
No role-differentiated access — single actor (Candidate).

### QA-Observable Behaviour
- A portal task requests a job from LinkedIn/Naukri/Glassdoor and creates a successful application record with a validated session and resume artifact.
- The browser worker pauses for takeover when CAPTCHA, MFA, or suspicious modal detection occurs.
- High-risk actions are blocked or require explicit user review.

### Prerequisites
- Story 7.1 completed.
- Story 8.1 completed.
- Story 9.1 completed.

### Implementation Steps

1. **Add vendor-specific connector implementations**
   - Create `LinkedInConnector`, `NaukriConnector`, and `GlassdoorConnector` under `backend/app/services/discovery/`.
   - Register these connectors in `ConnectorRegistry`.
   - Implement `search_jobs`, `apply`, and session validation methods with provider-aware error handling.

2. **Add portal-aware session handling**
   - Use session vault payloads to restore cookies, local storage, and browser state before automation.
   - Add session health checks for each provider.
   - Refresh stale sessions without disrupting the user workflow.

3. **Extend the browser automation runtime**
   - Update `PlaywrightBrowserCore` to detect `linkedin`, `naukri`, `glassdoor`, and career-page form variants.
   - Add smarter selectors for common fields: name, email, phone, resume upload, work authorization, and custom questions.
   - Add retry/backoff and timeout handling for dynamic pages.

4. **Implement safety constraints and user approval gates**
   - Block or require review for suspicious/anti-bot pages.
   - Enforce per-site rate limits and cool-down windows.
   - Support `pause`, `resume`, and `stop` workflows before risky submits.
   - Keep a per-application audit record for all runtime decisions.

5. **Integrate takeover support for challenges**
   - Detect CAPTCHA, MFA, or non-standard form blockers.
   - Pause the worker and notify the user for takeover.
   - Resume the same automation task after manual interaction.

6. **Add browser profile support for real Chrome usage**
   - Support dedicated browser profiles per portal with separate `user_data_dir` and persistent cookies.
   - Ensure the automation can launch the target Chrome profile without leaking session state between portals.

7. **Update frontend controls**
   - Add portal selection and connection validation in the Account Hub.
   - Add runtime status cards for session health, rate-limit state, and takeover required state.

### Test Requirements
- Unit tests verifying all new portal connectors implement the connector contract.
- Integration test verifying `LinkedInConnector` session validation and job search placeholder/real parsing behavior.
- Integration test verifying `GlassdoorConnector` and `NaukriConnector` return provider-specific structured output without crashing.
- End-to-end browser automation test covering a mock LinkedIn/Naukri/Glassdoor page and validating resume upload plus submission state.
- Safety test verifying CAPTCHA/MFA challenge triggers takeover mode and pauses the worker instead of submitting prematurely.

### Quality Checks
- Ruff/typing compliance.
- No plaintext secrets in logs.
- Application session recovery is resilient to stale cookies and re-auth flows.
- Simulation must fail safe and never auto-submit on unknown/unsafe pages.

### Completion Evidence
- Pytest suite passing.
- At least one integration test covering LinkedIn/Naukri/Glassdoor-style automation flow.
- Manual verification of portal detection and session restore on a mock browser job page.
