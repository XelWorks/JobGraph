# Story 3.1: Discovery connector framework


**Must Read**:
- `docs/requirements.md` - Greenhouse and Lever integration requirements

**Description**:
Create the extensible job discovery connector framework. Implement concrete integration logic to pull/scrape job details from Greenhouse and Lever ATS boards and store job metadata inside PostgreSQL database.

**Acceptance Criteria**:
- Base class `BaseConnector` defines common interfaces.
- `GreenhouseConnector` and `LeverConnector` correctly parse job titles, descriptions, and metadata.
- Scheduler job (FastAPI background tasks / Celery wrapper) runs connectors regularly.
- Deduplicates jobs based on ATS board key and job identifier.

**Prerequisites**:
- Story 1.1 and 1.3 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- Clean architecture domain interfaces

**Implementation Steps**:
1. Define JobPosting PostgreSQL model.
2. Implement connector base and concrete classes in `backend/app/services/discovery/connector.py`.
3. Set up scheduler loop wrapper.

**Test Requirements**:
- Scraper tests with cached HTML mock responses to avoid live network dependencies.
- Deduplication logic tests.

**Quality Checks**:
- Connectors fail gracefully if an ATS board structure changes.

**Out of Scope**:
- Advanced scraper bypassing (Cloudflare bypasses) in this story.

**Completion Evidence**:
- Scraper tests run successfully.
