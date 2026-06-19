# Story 1.2: Frontend skeleton


**Must Read**:
- `docs/requirements.md` - Approved requirements
- `docs/architecture/design/00-system-architecture-greenfield.md` - System design
- `docs/architecture/design/01-patterns-and-standards-greenfield.md` - Frontend layout standards

**Description**:
Bootstrap the frontend React application layout using Next.js (App Router). Set up the project directory structures, layout shell (sidebar, navigation, content viewport), TailwindCSS utility styling, and config structures.

**Acceptance Criteria**:
- Next.js application boots successfully without build errors.
- Sidebar contains navigation links for Dashboard, Profile, Job discovery, Applications, and Settings.
- TailwindCSS styling is correctly imported and working.
- Page layouts are responsive (work on both desktop and mobile viewports).

**Prerequisites**:
- Story 1.0 (Root tooling seed) must be completed.

**Context Files to Read**:
- `docs/architecture/design/00-system-architecture-greenfield.md`

**Patterns to Follow**:
- Folder layout structure: `frontend/app/`, `frontend/components/`, `frontend/features/`

**Implementation Steps**:
1. Scaffold Next.js application structure inside `frontend/` directory.
2. Setup `frontend/app/layout.tsx` to include the navigation sidebar and layout container.
3. Setup `frontend/app/page.tsx` with a dashboard overview layout.
4. Verify Tailwind styling is imported in `frontend/app/globals.css`.

**Test Requirements**:
- Next.js development build finishes cleanly (`npm run build` exits 0).
- Visual check of desktop layout viewport and navigation.

**Quality Checks**:
- TypeScript compiler (`tsc`) runs with no errors.
- ESLint checks pass with 0 errors.

**Out of Scope**:
- Communication with the backend API or any stateful data queries.

**Completion Evidence**:
- Running local Next.js build shows 0 errors.
