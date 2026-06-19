---
cr-id: CR-1
status: applied
introduced-by: "docs/requirements.md::## Technical Constraints"
impacts-requirements: ["## Technical Constraints", "## Explicit Scope", "## Timeline"]
impacts-stories: [epic-1-story-1.1-backend-skeleton]
impacts-epics: [Epic-1]
cycle-introduced: null
scheduled-cycle: null
primary-epic: Epic-1
introduces-epic: Epic-7
approval-authority: pdm
rationale: |
  Frontend framework transition from Next.js to React JS client-side SPA.
  CORS middleware description in backend skeleton story epic-1-story-1.1 refers to Next.js;
  this story has status: done and is frozen; delta requires CR-supersede.
applies-against-shipped: true
evidence-links: ["file:///C:/Users/gourav.g/Desktop/Job%20Applier/docs/stories-implemented/story-1.1-review.md"]
applied-at: "2026-06-19T17:40:00Z"
applied-by: "Gourav G"
produced-by: "requirements-steward@v1.0.0 Mode A"
---

# Change Request 1: Frontend Framework Transition to React JS

## Summary
Transition the frontend application framework from Next.js (Server-Side Rendering) to React JS (Client-Side Single Page Application). This updates the technical constraints and Explicit Scope of the project requirements, and supersedes the completed Backend skeleton story to reference the updated client.

## Impact analysis
- **Requirements affected**: Technical Constraints (Frontend Framework), Explicit Scope (IN Scope), Timeline (Implementation Complete deliverables).
- **Stories affected**: `epic-1-story-1.1-backend-skeleton` (completed).
- **Behavioral changes**: Backend CORS allowed origins policy is mapped to a React JS client SPA. No code changes are required on the backend since CORS allowed origins are dynamically loaded from environment settings.
- **Metadata-only updates**: (none)

## Dependency impact
No dependency cycles are introduced. The React client-side application will still communicate with the same FastAPI backend API endpoints.

## Resolution
Story epic-1-story-1.1 is replaced by CR-1.1. In-place revisions are applied to epic-1-story-1.2, epic-2-story-2.3, epic-3-story-3.3.

## Approval
| Role | Name | Status | Date |
| :--- | :--- | :----- | :--- |
| Product Manager | ANALYST_PM_GREENFIELD | Approved | 2026-06-19 |
| Tech Lead | ARCHITECT | Approved | 2026-06-19 |

## Closure
The following files were modified to apply this Change Request:
- `docs/requirements.md`
- `docs/plans/stories/epic-1-story-1.2-frontend-skeleton.md`
- `docs/plans/stories/epic-2-story-2.3-auth-and-profile-ui.md`
- `docs/plans/stories/epic-3-story-3.3-discovery-and-scoring-dashboard.md`
- `docs/architecture/design/00-system-architecture-greenfield.md`
- `docs/architecture-diagrams/00-system-architecture-diagrams-greenfield.md`
- `docs/plans/implementation-plan.md`
- `docs/plans/stories/epic-1-story-1.1-backend-skeleton.md` (superseded audit-write)
- `docs/status.md`
