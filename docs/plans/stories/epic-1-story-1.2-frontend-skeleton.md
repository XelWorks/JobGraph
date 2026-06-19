# Story 1.2: Frontend skeleton

**Developer**: Dev 2

**Must Read**:
- `docs/requirements.md` - Approved requirements
- `docs/architecture/design/00-system-architecture-greenfield.md` - System design
- `docs/architecture/design/01-patterns-and-standards-greenfield.md` - Frontend layout standards

**Description**:
Bootstrap the frontend React application layout using React JS (Vite/SPA). Set up the project directory structures, layout shell (sidebar, navigation, content viewport), TailwindCSS utility styling, and config structures.

**Acceptance Criteria**:
- React JS application boots successfully without build errors.
- Sidebar contains navigation links for Dashboard, Profile, Job discovery, Applications, and Settings.
- TailwindCSS styling is correctly imported and working.
- Page layouts are responsive (work on both desktop and mobile viewports).

**Prerequisites**:
- Story 1.0 (Root tooling seed) must be completed.

**Context Files to Read**:
- `docs/architecture/design/00-system-architecture-greenfield.md`

**Patterns to Follow**:
- Folder layout structure: `frontend/src/`, `frontend/src/components/`, `frontend/src/features/`

**Implementation Steps**:
1. Scaffold React JS application structure (using Vite or similar) inside `frontend/` directory.
2. Setup `frontend/src/main.tsx` and `frontend/src/App.tsx` to include the navigation sidebar and layout container.
3. Setup `frontend/src/features/dashboard/` with a dashboard overview layout.
4. Verify Tailwind styling is imported.

**Test Requirements**:
- React JS development build finishes cleanly (`npm run build` exits 0).
- Visual check of desktop layout viewport and navigation.

**Quality Checks**:
- TypeScript compiler (`tsc`) runs with no errors.
- ESLint checks pass with 0 errors.

**Out of Scope**:
- Communication with the backend API or any stateful data queries.

**Completion Evidence**:
- Running local React JS build shows 0 errors.

---

## Change log

### 2026-06-19 — Updated for technical-constraints@v1.1

**Trigger:** drift run; entry-mode 2A plain-English.
**Pre-edit status:** planned   ← R14(b) carve-out

**Sections modified:**
- `## Description` — Transitioned from Next.js to React JS layout setup.
- `## Acceptance Criteria` — Updated to verify React JS build and framework.
- `## Implementation Steps` — Refactored steps to use Vite React layout files.
- `## Test Requirements` — Updated build verification.
- `## Completion Evidence` — Updated compilation log assertions.

**Delta:**

| Aspect | Before | After |
| :-- | :-- | :-- |
| Framework | Next.js (App Router) | React JS (Vite) |
| Layout Entrypoint | `frontend/app/layout.tsx` | `frontend/src/App.tsx` |

**Reason no CR was drafted:** foundation story was `status: planned` at edit time (R14(b) carve-out — no shipped or in-flight code to preserve).