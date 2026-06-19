# Story 5.3: Tracking and reporting UI

**Developer**: Dev 2

**Must Read**:
- `docs/requirements.md` - Application tracking records

**Description**:
Build the application funnel tracking interface. Enable candidates to see their queue of submissions, log results, edit statuses, and review metrics charts.

**Acceptance Criteria**:
- Page lists applied jobs with their status: Backlog, Scheduled, Auto-Filled, Submitted, Failed.
- Shows links to tailored documents used for the application.
- Offers dashboard graphs (jobs found, matched, applied).

**Prerequisites**:
- Story 1.2, 5.1, 5.2 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- User UI charts and metrics presentation

**Implementation Steps**:
1. Create table component in `frontend/features/applications/TrackingTable.tsx`.
2. Connect to endpoint `/api/v1/applications`.
3. Design dashboard reports.

**Test Requirements**:
- Client renders application list data correctly.

**Quality Checks**:
- Secure links to PDFs render and work in the UI table.

**Out of Scope**:
- Analytics integrations with external tools.

**Completion Evidence**:
- Component rendering validations.