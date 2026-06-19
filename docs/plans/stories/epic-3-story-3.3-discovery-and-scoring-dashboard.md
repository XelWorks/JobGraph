# Story 3.3: Discovery and scoring dashboard

**Developer**: Dev 2

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
1. Create feed pages and sub-components inside `frontend/src/features/jobs/`.
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
- React JS rendering verification logs.

---

## Change log

### 2026-06-19 — Updated for technical-constraints@v1.1

**Trigger:** drift run; entry-mode 2A plain-English.
**Pre-edit status:** planned   ← R14(b) carve-out

**Sections modified:**
- `## Completion Evidence` — Updated verification log description to React JS.

**Delta:**

| Aspect | Before | After |
| :-- | :-- | :-- |
| Completion Evidence | Next.js logs | React JS logs |

**Reason no CR was drafted:** foundation story was `status: planned` at edit time (R14(b) carve-out — no shipped or in-flight code to preserve).