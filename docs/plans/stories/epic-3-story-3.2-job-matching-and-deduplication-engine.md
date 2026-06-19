# Story 3.2: Job matching and deduplication engine


**Must Read**:
- `docs/requirements.md` - Job Matching & Scoring Engine rules

**Description**:
Implement the scoring algorithms mapping discovered jobs against the candidate profile. Scoring weights: Skill (40%), Experience (30%), Location (15%), and Salary (15%).

**Acceptance Criteria**:
- Calculates overall score out of 100.
- Jobs scoring below threshold (default 70) are auto-archived.
- Utilizes simple keyword matching and basic semantic evaluation.
- Persists computed match scores inside `MATCH_SCORE` table.

**Prerequisites**:
- Story 3.1 and 2.2 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- Business rules encapsulation in service layers

**Implementation Steps**:
1. Implement scoring module `backend/app/services/matching/scoring.py`.
2. Wire matching triggers during the job discovery ingestion pipeline.
3. Save matching breakdown records to DB.

**Test Requirements**:
- Tests matching various sample job postings against sample profiles and verifying expected score results.

**Quality Checks**:
- Clean handling of edge cases (missing job fields, empty profiles).

**Out of Scope**:
- Complex deep AI evaluations (rely on simple NLP/keyword/metadata scoring for MVP).

**Completion Evidence**:
- Executable unit tests validating the scoring weights.
