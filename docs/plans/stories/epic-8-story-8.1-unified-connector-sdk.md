# Story 8.1: Unified Connector SDK

**BUILDID**: NO-CYCLE | **Epic**: 8 - BROWSER PROFILE & CONNECTOR SDK | **ID**: 8.1 | **Date**: 2026-07-29 | **Jira**: LOCAL  
**Wave**: 13 | **Requires**: [3.1, 6.1] | **Enables**: [8.2, 8.3, 9.1]  
**Files Touched**: `backend/app/domain/connector.py`, `backend/app/services/discovery/connector_sdk.py`  
**Roles Ref**: Candidate  
**QA Candidate**: Yes — Observable: Standardized connector interface methods; Mechanism: Python abstract base class and SDK implementation; Authz & preconditions: Internal service context; Edge & idempotency: Unified exception handling for all connectors; Regression: Greenhouse and Lever discovery.

---

## 👤 User Reference

### Description
Establish a **Unified Connector SDK** standardizing job portal interactions across all ATS platforms and job boards. Every portal connector (Greenhouse, Lever, LinkedIn, Workday, Naukri) exposes the exact same standardized methods (`connect`, `disconnect`, `validate_session`, `search_jobs`, `apply`, `health_check`, `refresh_session`), insulating the core application from provider-specific DOM or API differences.

### Acceptance Criteria
- Abstract base class `BasePortalConnector` defines uniform contract methods.
- Refactors Greenhouse and Lever discovery connectors to implement the Unified Connector SDK interface.
- Exposes standardized session health check and session refresh methods.
- Keeps core business logic completely independent of job board implementations.

---

## 🤖 AI Agent Reference

### Context Files to Read
- `docs/architecture/design/00-system-architecture-greenfield.md`
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

### RBAC Enforcement
No role-differentiated access — single actor (Candidate).

### QA-Observable Behaviour
- All portal connectors inherit from `BasePortalConnector` and implement `connect()`, `disconnect()`, `validate_session()`, `search_jobs()`, `apply()`, `health_check()`, and `refresh_session()`.

### Prerequisites
- Story 3.1 and Story 6.1 completed.

### Implementation Steps

1. **Define Abstract Interface (`backend/app/domain/connector.py`)**:
   ```python
   from abc import ABC, abstractmethod
   from typing import Any, Dict, List

   class BasePortalConnector(ABC):
       @abstractmethod
       async def connect(self, session_data: Dict[str, Any]) -> bool:
           pass

       @abstractmethod
       async def disconnect(self) -> None:
           pass

       @abstractmethod
       async def validate_session(self) -> bool:
           pass

       @abstractmethod
       async def search_jobs(self, query: str, location: str) -> List[Dict[str, Any]]:
           pass

       @abstractmethod
       async def apply(self, job_url: str, profile_data: Dict[str, Any], resume_path: str) -> Dict[str, Any]:
           pass

       @abstractmethod
       async def health_check(self) -> str:
           pass

       @abstractmethod
       async def refresh_session(self) -> Dict[str, Any]:
           pass
   ```

2. **Implement Connector SDK Manager (`backend/app/services/discovery/connector_sdk.py`)**:
   - Wrap Greenhouse, Lever, and future portal connectors under `ConnectorRegistry`.
   - Provide factory lookup `ConnectorRegistry.get_connector(platform_name)`.

### Test Requirements
- Unit tests verifying interface compliance for all registered connectors.

### Quality Checks
- Clean typing annotations and Ruff linter compliance.

### Completion Evidence
- Pytest suite passing with 0 errors.
