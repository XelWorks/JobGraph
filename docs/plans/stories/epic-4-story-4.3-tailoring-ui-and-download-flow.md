# Story 4.3: Tailoring UI and download flow

**Developer**: Dev 2

**Must Read**:
- `docs/requirements.md` - PDF/Document download options

**Description**:
Build the user-facing workspace interface enabling candidates to view tailoring results, compare modifications, edit sections, and download final PDFs.

**Acceptance Criteria**:
- Screen displays Side-by-Side comparison of original vs tailored bullets.
- Action button to trigger PDF generation and download.
- Fetches secure, temporary pre-signed MinIO URL keys for client downloads.

**Prerequisites**:
- Story 1.2, 4.1, 4.2 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- File serving controls

**Implementation Steps**:
1. Create tailoring preview panel in `frontend/features/tailoring/TailorPanel.tsx`.
2. Connect download actions to secure S3 URLs fetch api.

**Test Requirements**:
- Test UI downloads fetch trigger requests.

**Quality Checks**:
- Secure download URLs expire as expected.

**Out of Scope**:
- Complex inline document editing tools (plain text inputs are fine).

**Completion Evidence**:
- Client logs showing download url generation success.