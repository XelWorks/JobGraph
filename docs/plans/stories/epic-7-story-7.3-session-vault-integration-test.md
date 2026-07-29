# Story 7.3: Session Vault Integration Test

**BUILDID**: NO-CYCLE | **Epic**: 7 - SESSION VAULT & ACCOUNT HUB | **ID**: 7.3 | **Date**: 2026-07-29 | **Jira**: LOCAL  
**Wave**: 14 | **Requires**: [7.1] | **Enables**: []  
**Files Touched**: `backend/tests/integration/test_vault.py`  
**Roles Ref**: Candidate  
**QA Candidate**: Yes — Observable: AES-256-GCM encryption and decryption round-trip; Mechanism: Pytest integration suite; Authz & preconditions: JWT authentication; Edge & idempotency: Multi-portal session rotation and teardown; Regression: Profile and Vault DB models.

---

## 👤 User Reference

### Description
Create an integration test verifying the Session Vault API and AES-256-GCM encryption pipeline. The test verifies registering session payloads, decrypting credentials for authorized automation workers, updating portal health statuses, and purging vault entries cleanly.

### Acceptance Criteria
- Pytest script runs and validates the complete Session Vault lifecycle.
- Asserts that session payloads are encrypted in PostgreSQL and decrypted correctly on read.
- Verifies unauthorized requests are rejected with 401 Unauthorized.
- Cleans up created vault test records after execution.

---

## 🤖 AI Agent Reference

### Context Files to Read
- `docs/architecture/design/00-system-architecture-greenfield.md`
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

### RBAC Enforcement
No role-differentiated access — single actor (Candidate).

### QA-Observable Behaviour
- `test_vault.py` passes 100% of assertions verifying encryption, decryption, health updates, and teardown.

### Prerequisites
- Story 7.1 completed.

### Implementation Steps

1. **Create Integration Test File (`backend/tests/integration/test_vault.py`)**:
   - Register a test user and obtain auth headers.
   - Post portal session payload to `/api/v1/vault`.
   - Read encrypted database column directly to verify AES-256-GCM cipher text.
   - Call `/api/v1/vault/{portal}/decrypt` to verify decrypted payload matches original.
   - Update portal health status and verify changes.
   - Delete portal entry and verify database cleanup in teardown block.

### Test Requirements
- Run `pytest backend/tests/integration/test_vault.py` and verify 100% pass.

### Quality Checks
- All database records and session keys removed during test teardown.

### Completion Evidence
- Pytest report showing `test_vault.py` passing cleanly.
