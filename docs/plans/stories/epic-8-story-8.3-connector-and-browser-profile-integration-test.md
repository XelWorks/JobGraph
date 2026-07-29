# Story 8.3: Connector & Browser Profile Integration Test

**BUILDID**: NO-CYCLE | **Epic**: 8 - BROWSER PROFILE & CONNECTOR SDK | **ID**: 8.3 | **Date**: 2026-07-29 | **Jira**: LOCAL  
**Wave**: 15 | **Requires**: [8.1, 7.1] | **Enables**: []  
**Files Touched**: `backend/tests/integration/test_connector_sdk.py`  
**Roles Ref**: Candidate  
**QA Candidate**: Yes — Observable: Unified connector SDK method executions; Mechanism: Pytest integration test; Authz & preconditions: Internal service context; Edge & idempotency: Connect, search, apply, and health check calls; Regression: Discovery connectors.

---

## 👤 User Reference

### Description
Create an integration test validating the Unified Connector SDK and Browser Profile integration. The test verifies that all connectors inheriting from `BasePortalConnector` implement uniform methods (`connect`, `disconnect`, `validate_session`, `search_jobs`, `apply`, `health_check`, `refresh_session`) and load encrypted session profiles cleanly from the Session Vault.

### Acceptance Criteria
- Pytest script tests connector instantiation via `ConnectorRegistry`.
- Verifies session validation and health check methods across all registered connectors.
- Asserts that session payloads from the Session Vault are applied correctly.

---

## 🤖 AI Agent Reference

### Context Files to Read
- `docs/architecture/design/00-system-architecture-greenfield.md`
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

### QA-Observable Behaviour
- `test_connector_sdk.py` passes 100% of assertions for Greenhouse and Lever connectors under the SDK registry.

### Prerequisites
- Story 8.1 and Story 7.1 completed.

### Implementation Steps

1. **Create Integration Test (`backend/tests/integration/test_connector_sdk.py`)**:
   - Instantiate connectors using `ConnectorRegistry.get_connector()`.
   - Call `health_check()` and `validate_session()`.
   - Mock portal discovery and form submission through the unified interface.

### Test Requirements
- Run `pytest backend/tests/integration/test_connector_sdk.py` and verify 100% pass.

### Completion Evidence
- Pytest console output showing clean pass.
