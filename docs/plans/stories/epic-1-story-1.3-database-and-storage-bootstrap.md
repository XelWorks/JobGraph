# Story 1.3: Database and storage bootstrap


**Must Read**:
- `docs/requirements.md` - Approved database tech constraints
- `docs/architecture/design/00-system-architecture-greenfield.md` - Datastore layouts

**Description**:
Establish the local database connection context (PostgreSQL via SQLAlchemy async engine) and bootstrap object storage connection (MinIO S3 adapter client). This story ensures that the persistence layer is testable and accessible by services.

**Acceptance Criteria**:
- Database connection session manager initializes correctly using `asyncpg`.
- PostgreSQL database connections are pooled and verified via a ping query.
- MinIO S3 client initializes using the configurations loaded from environment.
- Local S3 bucket is created automatically on startup if it doesn't already exist.

**Prerequisites**:
- Story 1.1 (Backend skeleton) must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- Database Access Pattern (through sessions/sessionmakers)

**Implementation Steps**:
1. Implement `backend/app/infrastructure/db/session.py` containing:
   - Async engine creation `create_async_engine`.
   - `async_sessionmaker` instantiation.
   - Dependency provider `get_db` yielding sessions.
2. Implement `backend/app/infrastructure/storage/minio.py` containing a class wrapper for the `boto3` or `miniopy` client, checking and creating default application buckets.

**Test Requirements**:
- Integration test attempting to query PostgreSQL (`SELECT 1`) using the session manager.
- Integration test attempting to list/create bucket in MinIO.

**Quality Checks**:
- Connections are properly closed after operations to avoid memory/socket leaks.

**Out of Scope**:
- Entity tables mapping, migrations index, or file upload logic.

**Completion Evidence**:
- Integration test outputs demonstrating clean DB connection and bucket verification.
