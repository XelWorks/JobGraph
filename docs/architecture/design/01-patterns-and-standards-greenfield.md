# Patterns & Standards - AutoApply AI

**Date**: 2026-06-19  
**Author**: ARCHITECT  
**Status**: Approved  
**Version**: 1.0

---

## Purpose

This document defines the coding, testing, configuration, documentation, and module-boundary standards for AutoApply AI. The goal is to keep the system cleanly layered, testable, secure, and easy for DEV to extend without breaking cross-cutting responsibilities.

---

## Project Structure

### Repository Layout

```text
frontend/
  app/
  components/
  features/
  lib/
  tests/
backend/
  app/
  api/
  core/
  domain/
  infrastructure/
  services/
  tests/
workers/
  jobs/
  schedulers/
shared/
  schemas/
  utils/
docs/
  architecture/
  plans/
  requirements.md
```

### Naming Conventions
- Use `snake_case` for Python modules and packages.
- Use `PascalCase` for Python classes and TypeScript React components.
- Use `camelCase` for TypeScript variables, functions, and hooks.
- Name files by responsibility, not by generic layer names.
- Prefer explicit module names such as `job_discovery_service.py`, `application_repository.py`, and `resume_tailoring_workflow.py`.

### File Organization Rules
- Keep one primary responsibility per file.
- Split modules once they exceed roughly 300-400 lines or mix concerns.
- Place application orchestration in `services/` or `workflows/`, not in route handlers.
- Keep API route handlers thin and free of business rules.

---

## Code Structure Standards

### Function and Class Design
- Functions should do one thing and fit on a single screen when possible.
- Prefer 3-4 parameters or fewer; use request objects for larger inputs.
- Use guard clauses for validation and failure checks.
- Keep business rules inside domain or use-case modules, not in controllers.

#### DO
```python
class JobMatchingService:
    def score_job(self, profile, job_posting):
        if not profile or not job_posting:
            raise ValueError("profile and job_posting are required")

        skill_score = self._score_skills(profile.skills, job_posting.required_skills)
        experience_score = self._score_experience(profile.experience_years, job_posting.min_experience)
        location_score = self._score_location(profile.preferred_locations, job_posting.location)
        salary_score = self._score_salary(profile.salary_expectation, job_posting.salary_range)

        return {
            "overall": self._weighted_total(skill_score, experience_score, location_score, salary_score),
            "skill_score": skill_score,
            "experience_score": experience_score,
            "location_score": location_score,
            "salary_score": salary_score,
        }
```

#### DON'T
```python
def score_job(profile, job_posting, db, logger, config, cache):
    if profile:
        if job_posting:
            if db:
                # too many responsibilities mixed together
                pass
```

### Import Ordering
- Standard library first.
- Third-party packages second.
- Local application imports last.
- Keep imports grouped and sorted.

#### DO
```python
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import JobPosting
from app.services.matching import JobMatchingService
```

#### DON'T
```python
from app.services.matching import JobMatchingService
import datetime
from fastapi import Depends, APIRouter, HTTPException
```

---

## Error Handling Pattern

### Standards
- Raise explicit custom exceptions for expected failures.
- Convert internal exceptions to structured API errors at the edge.
- Log technical details once, but return safe user-facing messages.
- Never swallow exceptions silently.

### Error Response Shape
```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "The requested job could not be found.",
    "request_id": "req_12345"
  }
}
```

#### DO
```python
class JobNotFoundError(Exception):
    pass


async def get_job(job_id: str, repository):
    job = await repository.find_by_id(job_id)
    if job is None:
        raise JobNotFoundError(f"Job {job_id} not found")
    return job


@router.get("/jobs/{job_id}")
async def read_job(job_id: str):
    try:
        job = await get_job(job_id, repository)
        return {"data": job}
    except JobNotFoundError:
        raise HTTPException(status_code=404, detail={"code": "JOB_NOT_FOUND"})
```

#### DON'T
```python
async def read_job(job_id: str):
    try:
        return await repository.find_by_id(job_id)
    except Exception:
        return None
```

---

## Logging Pattern

### Standards
- Use structured JSON logs.
- Include `request_id`, `user_id` when present, `component`, and `event_name`.
- Use `info` for business milestones, `warning` for recoverable issues, `error` for failures.
- Never log passwords, API keys, resume contents, or raw browser secrets.

#### DO
```python
logger.info(
    "job_scored",
    extra={
        "request_id": request_id,
        "user_id": user_id,
        "job_id": job_id,
        "match_score": match_score,
        "component": "matching_service",
    },
)
```

#### DON'T
```python
logger.info(f"User {email} logged in with password {password}")
```

---

## Database Access Pattern

### Standards
- All database access goes through repositories.
- Use parameterized queries or ORM-bound parameters only.
- Use explicit transaction boundaries for multi-step writes.
- Keep data mapping separate from business rules.

#### DO
```python
class ApplicationRepository:
    def __init__(self, session):
        self._session = session

    async def save(self, application):
        self._session.add(application)
        await self._session.flush()
        return application
```

#### DON'T
```python
async def save_application(application):
    await session.execute(
        f"INSERT INTO applications VALUES ('{application.id}', '{application.status}')"
    )
```

### Transaction Pattern
```python
async with session.begin():
    await application_repository.save(application)
    await audit_repository.record_event(event)
```

---

## API Design Pattern

### Standards
- Use versioned APIs under `/api/v1`.
- Validate request bodies with Pydantic schemas.
- Return consistent JSON envelopes for success and errors.
- Keep route handlers thin; delegate to services.
- Require authentication on user-specific endpoints.

#### DO
```python
@router.post("/applications/apply", status_code=202)
async def apply_to_job(request: ApplyRequest, service: ApplicationService = Depends()):
    result = await service.start_application(request.job_id, request.mode)
    return {"status": "accepted", "data": result}
```

#### DON'T
```python
@router.post("/applications/apply")
async def apply_to_job(payload: dict):
    # validates, scores, stores, tailors, and submits all in the router
    pass
```

### Response Convention
- Success: `{ "status": "success", "data": ... }`
- Accepted async work: `{ "status": "accepted", "data": ... }`
- Error: `{ "error": { "code": "...", "message": "..." } }`

---

## Configuration Pattern

### Standards
- Read configuration from environment variables only.
- Keep defaults in a dedicated config object.
- Centralize secrets handling and encryption key loading.
- Never commit `.env` files or secrets into source control.

#### DO
```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    valkey_url: str
    minio_endpoint: str
    gemini_api_key: str
    app_env: str = "development"

    class Config:
        env_file = ".env"
```

#### DON'T
```python
DATABASE_URL = "postgresql://user:password@localhost:5432/app"
GEMINI_API_KEY = "hardcoded-secret"
```

---

## Unit Test Pattern

### Standards
- Place tests adjacent to the module or in mirrored `tests/` directories.
- Follow AAA: Arrange, Act, Assert.
- Name tests after behavior, not implementation details.
- Mock external systems, not domain logic.

#### DO
```python
async def test_score_job_returns_high_match_for_aligned_profile():
    # Arrange
    service = JobMatchingService()
    profile = make_profile(skills=["Python", "FastAPI"])
    job = make_job(required_skills=["Python", "FastAPI"])

    # Act
    result = service.score_job(profile, job)

    # Assert
    assert result["overall"] >= 80
```

#### DON'T
```python
async def test_foo():
    assert True
```

---

## Integration Test Pattern

### Standards
- Use a real ephemeral database or containerized test dependency.
- Mock only third-party services that are not under test.
- Reset state between tests.
- Verify the full request path through API, service, and repository layers.

#### DO
```python
async def test_create_application_persists_record(test_client, test_db):
    response = await test_client.post(
        "/api/v1/applications/apply",
        json={"job_id": "job-1", "mode": "Assisted"},
    )

    assert response.status_code == 202
    assert await test_db.application_exists("job-1")
```

#### DON'T
```python
async def test_apply_endpoint(monkeypatch):
    monkeypatch.setattr("repository.save", lambda *_: None)
    assert True
```

---

## Coverage Requirements

### Standards
- Minimum unit test coverage is **85%**.
- Cover success paths, validation failures, and security-sensitive branches.
- Test all public APIs, orchestration flows, and repository error paths.
- Coverage enforcement must run in CI.

### What to Skip
- Trivial data containers with no logic.
- Third-party library internals.
- Generated framework code unless custom logic exists.

---

## Documentation Standards

### Standards
- Document public APIs with concise docstrings.
- Use comments only when the reason is not obvious from the code.
- Keep READMEs focused on setup, architecture, run, and test instructions.
- Keep generated docs in `docs/` and reference them from the relevant workflow outputs.

#### DO
```python
async def generate_cover_letter(profile, job_description):
    """Generate an ATS-friendly cover letter for a specific job posting."""
    ...
```

#### DON'T
```python
# This function generates a cover letter
async def generate_cover_letter(profile, job_description):
    ...
```

---

## File / Module Boundary Map

### Authoritative Ownership Map

| Concern | Owning Files / Globs | Notes |
|---------|----------------------|-------|
| Authentication | `backend/app/api/auth/*.py`, `backend/app/services/auth/*.py`, `backend/app/domain/auth/*.py` | Owns login, registration, token issuance, password hashing. |
| User Profiles | `backend/app/api/profiles/*.py`, `backend/app/services/profiles/*.py`, `backend/app/domain/profiles/*.py` | Owns candidate profile CRUD, resume upload metadata, and preferences. |
| Job Discovery | `backend/app/services/discovery/*.py`, `workers/jobs/discovery/*.py` | Owns ATS search orchestration and deduplication. |
| Job Matching | `backend/app/services/matching/*.py`, `backend/app/domain/matching/*.py` | Owns scoring logic and threshold checks. |
| Resume Tailoring | `backend/app/services/tailoring/*.py`, `workers/jobs/tailoring/*.py` | Owns Gemini prompts and tailored document generation. |
| Application Execution | `backend/app/services/applications/*.py`, `workers/jobs/apply/*.py`, `backend/app/infrastructure/browser/*.py` | Owns application state transitions and browser automation flows. |
| Reporting | `backend/app/services/reporting/*.py`, `backend/app/api/reports/*.py` | Owns daily/weekly summaries and metrics aggregation. |
| API Routing | `backend/app/api/*.py`, `backend/app/main.py` | Owns route registration and request lifecycle hooks. |
| Domain Models | `backend/app/domain/**/*.py` | Owns pure business entities and value objects. |
| Shared Schemas | `shared/schemas/*.py`, `shared/schemas/*.ts` | Owns request/response contracts shared across layers. |
| Frontend UI | `frontend/app/**`, `frontend/components/**`, `frontend/features/**` | Owns dashboard screens and feature components. |
| Configuration | `backend/app/core/config.py`, `frontend/lib/config.ts`, `.env*` | Owns environment loading and feature flags. |
| Persistence | `backend/app/infrastructure/db/*.py`, `backend/app/infrastructure/storage/*.py` | Owns SQLAlchemy sessions, repositories, and MinIO adapters. |
| Observability | `backend/app/infrastructure/logging/*.py`, `backend/app/infrastructure/metrics/*.py` | Owns logging and metrics plumbing. |
| Tests | `backend/tests/**`, `frontend/tests/**`, `workers/tests/**` | Mirrors the code organization and keeps unit/integration boundaries explicit. |

### Shared Files
These files can legitimately be touched by multiple concerns and should be treated as cross-cutting in planning:
- `backend/app/main.py` - application bootstrap and router registration.
- `backend/app/core/config.py` - environment and secrets loading.
- `backend/app/api/__init__.py` - route registry.
- `backend/app/infrastructure/db/session.py` - database session factory.
- `backend/app/infrastructure/logging/logger.py` - structured logging setup.
- `shared/schemas/*.py` - contract definitions used by frontend and backend.
- `package.json` / `pyproject.toml` / lockfiles - dependency management.
- `docker-compose.yml` - local deployment graph and service wiring.

### Unavoidable Cross-Concern Files
- `backend/app/main.py` must register auth, profile, discovery, matching, tailoring, application, and reporting routes because the application needs a single bootstrap point.
- `backend/app/core/config.py` must expose environment values to all runtime layers.
- Shared schema packages must be consumed by both API handlers and client code to avoid contract drift.

---

## Quality Checklist

- [ ] Modules have one primary responsibility.
- [ ] Route handlers stay thin and delegate to services.
- [ ] Database access goes through repositories.
- [ ] Logging is structured and redacted.
- [ ] Secrets come from configuration, not source code.
- [ ] Unit tests follow AAA and avoid over-mocking.
- [ ] Integration tests cover real request flows.
- [ ] Coverage remains at or above 85%.
- [ ] Public APIs are documented with docstrings or OpenAPI.
- [ ] Cross-concern files are limited to bootstrap and shared contracts only.

---

## Decision Summary

- Use clean architecture boundaries to keep business logic independent of framework details.
- Standardize on structured JSON logging and safe error envelopes for all APIs.
- Treat repositories as the only gateway to persistence.
- Keep configuration centralized and secrets externalized.
- Use mirrored tests and explicit ownership maps to prevent accidental coupling across features.
