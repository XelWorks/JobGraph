# Story 6.1: Observability and deployment hardening

**Developer**: Dev 2

**Must Read**:
- `docs/requirements.md` - Production-Ready MVP target
- `docs/architecture/design/00-system-architecture-greenfield.md` - Deployment

**Description**:
Harden the containerized setup and prepare for local/remote deployment. Set up structured JSON logging, redact secrets from trace files, configure Docker health checks, and secure PostgreSQL/MinIO network scopes.

**Acceptance Criteria**:
- Logs are exported as structured JSON format.
- Configuration variables ensure secrets (e.g. passwords, keys) are not leaked in log output.
- Docker compose containers run cleanly with healthy status flags.
- Databases do not expose ports to non-localhost networks when run inside Compose.

**Prerequisites**:
- Story 1.1, 1.2, 1.3 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- Logging standards, security configurations

**Implementation Steps**:
1. Implement structured JSON formatter in `backend/app/infrastructure/logging/logger.py`.
2. Redact sensitive fields.
3. Configure `docker-compose.yml` with healthchecks, environment links, and network bindings.

**Test Requirements**:
- Verify containers launch and status becomes 'healthy' on Docker Compose.
- Assert logs contain valid JSON format records.

**Quality Checks**:
- All keys are externalized.

**Out of Scope**:
- Kubernetes manifests.

**Completion Evidence**:
- Console logs showing Docker Compose status healthy.