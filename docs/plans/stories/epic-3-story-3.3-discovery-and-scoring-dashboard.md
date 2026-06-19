# Story 3.3: Discovery and scoring dashboard


**Must Read**:
- `docs/requirements.md` - Discovered Jobs Feed page

**Description**:
Create the dashboard view containing the feed of matched jobs. Users must be able to see the match scores, filter lists, and initiate applications.

**Acceptance Criteria**:
- Feed page queries `/api/v1/jobs` and lists results in a table/grid.
- Shows company, role, location, matching score, and discovery date.
- Contains scoring breakdown indicators (visual progress bars/tooltips).
- Button to trigger custom application tailoring/submission workflows.

**Prerequisites**:
- Story 1.2 and 3.2 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- UI specs, visual indicators, dynamic lists

**Implementation Steps**:
1. Create feed pages and sub-components inside `frontend/features/jobs/`.
2. Connect client pages to API routes.
3. Implement score filters and sorting select boxes.

**Test Requirements**:
- Frontend components render mock job data accurately.
- Score filter removes items scoring below criteria from client viewport.

**Quality Checks**:
- Beautiful UI, responsive tables, loading/empty states checked.

**Out of Scope**:
- Real application execution triggers (handled in Epic 5).

**Completion Evidence**:
- Next.js rendering verification logs.
