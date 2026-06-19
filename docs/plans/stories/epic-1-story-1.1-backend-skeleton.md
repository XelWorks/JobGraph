---
story-id: epic-1-story-1.1-backend-skeleton
epic: Epic-1
cycle: N/A
status: done
superseded-by:
  - CR-1.1
last-audit:
  date: "2026-06-19"
  result: pass
---
# Story 1.1: Backend skeleton

**Developer**: Dev 1

**Must Read**:
- `docs/requirements.md` - Approved requirements
- `docs/architecture/design/00-system-architecture-greenfield.md` - Clean architecture guidelines
- `docs/architecture/design/01-patterns-and-standards-greenfield.md` - FastAPI conventions, settings structure, and imports sorting

**Description**:
Create the backend FastAPI application scaffolding, configuration system, and base API gate layout. This story establishes the main entrypoint, initializes CORS and basic middlewares, provides a configuration loading module backed by Pydantic settings, and sets up a standard health check endpoint.

**Acceptance Criteria**:
- FastAPI application initializes successfully without errors.
- Base configurations (environment variables) are parsed safely using Pydantic Settings.
- A GET `/health` endpoint is exposed and returns `{"status": "healthy"}` with a `200 OK` status code.
- CORS middleware is configured to allow requests from the local Next.js client URL.
- Application structured logging is loaded during startup.

**Prerequisites**:
- Story 1.0 (Root tooling seed) must be completed.

**Context Files to Read**:
- `docs/architecture/design/00-system-architecture-greenfield.md`
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- Configuration Pattern (settings loaded from environment via Pydantic)
- Error Handling Pattern (standardized envelope on exception)

**Implementation Steps**:
1. Create `backend/app/core/config.py` using `BaseSettings` to manage environment configurations:
   ```python
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       app_name: str = "AutoApply AI API"
       app_env: str = "development"
       debug: bool = True
       allowed_origins: list[str] = ["http://localhost:3000"]
       database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/autoapply"
       valkey_url: str = "redis://localhost:6379/0"
       minio_endpoint: str = "localhost:9000"
       gemini_api_key: str = "mock-key-for-now"

       class Config:
           env_file = ".env"
   ```
2. Create `backend/app/api/__init__.py` to serve as the router barrel file.
3. Create the bootstrap application file `backend/app/main.py` with FastAPI initialization, CORS middleware, and GET `/health` endpoint.

**Test Requirements**:
- Unit test using FastAPI `TestClient` verifying the `/health` endpoint returns 200 and `{"status": "healthy"}`.
- Manual test accessing `/health` via browser/curl.

**Quality Checks**:
- Python files pass format and lint checks (`black`, `ruff`).
- No credentials or sensitive API keys are hardcoded in the settings class.

**Out of Scope**:
- Database connection tests or actual service dependencies beyond config initialization.

**Completion Evidence**:
- Test logs showing `pytest backend/tests/test_main.py` passes cleanly.