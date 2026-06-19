# Story 1.4: Shell-to-service health wiring

**Developer**: Dev 2

**Must Read**:
- `docs/architecture/design/00-system-architecture-greenfield.md` - Web connectivity

**Description**:
Create the initial client-server connection check. Integrate the frontend UI to query the backend's `/health` endpoint and verify the database and storage availability, showing connection status indicators in the dashboard header.

**Acceptance Criteria**:
- Frontend fetches `/health` status from backend API using async requests.
- Header displays a clear indicator badge: "Backend: Online" (green) or "Offline" (red).
- The dashboard page loads the health details (DB status, MinIO status) dynamically.

**Prerequisites**:
- Story 1.1, 1.2, 1.3 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- Standard dashboard UI guidelines

**Implementation Steps**:
1. In FastAPI backend, update `/health` to query PostgreSQL and MinIO status.
2. Create frontend component `frontend/components/HealthCheck.tsx` using `fetch` or `react-query`.
3. Integrate the component in `frontend/app/page.tsx` and header dashboard bar.

**Test Requirements**:
- Frontend rendering test checking if health badge appears.
- Mocking a backend failure shows "Offline" state in UI.

**Quality Checks**:
- No console errors on frontend during layout rendering.

**Out of Scope**:
- User accounts or authentication mechanisms.

**Completion Evidence**:
- Screenshot or browser test output validating health check visualization.