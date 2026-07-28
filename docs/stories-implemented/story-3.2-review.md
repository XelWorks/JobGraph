# Story 3.2 Self-Review: Job matching and deduplication engine

**Date**: 2026-07-28  
**Story**: Story 3.2: Job matching and deduplication engine  
**Developer**: DEV Agent  

---

## What Was Implemented

- **MatchScore Database Model (`backend/app/domain/job.py`)**:
  - Designed the SQLAlchemy database model schema for `MatchScore` tables.
  - Linked model structures dynamically via cascading `relationship` attributes to the parent `JobPosting` record model.
- **Scoring and Evaluation Algorithm Service (`backend/app/services/matching/scoring.py`)**:
  - Implemented the scoring algorithm mapping discovered jobs against the candidate profile using specified weights:
    - **Skill Match (40% weight)**: Compares profile skills against job descriptions and titles using word-boundary matching, with special alias checking rules (such as mapping PostgreSQL to Postgres).
    - **Experience Match (30% weight)**: Checks job titles against preferred roles (full matching and partial word checking).
    - **Location Match (15% weight)**: Matches job location strings against preferred locales, with special telecommute/remote matching rules.
    - **Salary Match (15% weight)**: Parses job descriptions for currency markers, comparing extracted maximum ranges against candidate targets (reverts to a neutral baseline score of 80 if no salary figures are found).
  - Enforces overall score ceilings and auto-archives job postings that fall below a given threshold (defaulting to `70`).
- **Comprehensive Unit Validations (`backend/tests/unit/test_matching_logic.py`)**:
  - Added unit test routines validating each scoring weight component independently (Skill, Experience, Location, Salary matching metrics, boundary edge cases, and defaults).
- **Multi-layered Matching Integration Tests (`backend/tests/integration/test_matching_flow.py`)**:
  - Developed a complete end-to-end matching integration test. Creates users and profiles, inserts job postings, fires scoring pipelines, asserts exact weighted point breakdowns, tests update-mode deduplications, and performs complete table teardowns.

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `backend/app/domain/job.py` | Modified | Defined SQL tables for `MatchScore` linked via relationships to `JobPosting` |
| `backend/app/main.py` | Modified | Registered `MatchScore` schema model dynamically to allow automatic database compiling on startup |
| `backend/app/services/matching/scoring.py` | New | Primary JobMatchingService class parsing weights, boundaries, and threshold archives |
| `backend/tests/unit/test_matching_logic.py` | New | Independent component validations for matching subsystems |
| `backend/tests/integration/test_matching_flow.py` | New | Complete end-to-end database, profile, job posting, and scoring pipeline integration tests |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| Business Rules Encapsulation | `scoring.py` | Kept scoring algorithms clean and decoupled from REST routes inside service wrappers. |
| In-Place Syncing | `scoring.py` | Updated existing MatchScore listings in-place, keeping status scores synced with database constraints. |
| Fallback Baselines | `scoring.py` | Returns neutral default baselines on missing data points rather than throwing exceptions. |

## Testing Summary

- **Unit/Integration Tests**: 4 new component unit validations, 1 new layered integration flow, **30 out of 30 total backend tests passing completely**.
- **Statement Coverage**: Backend test suite achieves **90%** statement coverage (target: ≥85%).
- **Lints & Style Rules**: Ruff linter executed successfully reporting exactly **0 errors and 0 warnings**.

**Pytest Executions**:
```text
pytest backend/tests/
..............................                                                                                       [100%]
30 passed, 29 warnings in 7.49s
```

## DoD Evidence

### Gate 1 — Spec Echo
- **Skill Match (40% weight)**: Verified in `test_calculate_skill_score` validating full and partial keyword-matching weights.
- **Experience Match (30% weight)**: Verified in `test_calculate_experience_score` testing role matching and partial word boundaries.
- **Location Match (15% weight)**: Verified in `test_calculate_location_score` verifying exact locations and remote targets.
- **Salary Match (15% weight)**: Verified in `test_calculate_salary_score` parsing salary markers and falling back to 80 on missing data.
- **Job matching integration**: Verified in `test_full_job_matching_ingestion_integration` asserting full score calculations, threshold rejections, update-mode changes, and clean table teardowns.

### Gate 2 — Negative-Space Check
- **No negative inputs**: Verified that `target_salary` validates against negative integers, and score boundaries are hard-constrained between `0` and `100`.
- **Zero linter warnings**: Verified Ruff checks ran successfully with 0 errors.

### Gate 3 — Contract Consistency
- **Entity Model Relations**: Checked database relationships between `JobPosting` and `MatchScore` to ensure cascading deletions align correctly.

---

## Next Steps

- [x] Ready for code review
- [x] Ready for Story 3.3: Discovery and scoring dashboard implementation
