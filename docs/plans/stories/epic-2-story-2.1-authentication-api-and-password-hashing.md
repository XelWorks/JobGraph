# Story 2.1: Authentication API and password hashing


**Must Read**:
- `docs/requirements.md` - Secure password hashing using Argon2
- `docs/architecture/design/00-system-architecture-greenfield.md` - Authentication & encryption handler

**Description**:
Implement the core authentication endpoints: user registration and login. Passwords must be hashed using Argon2, and authenticated requests must be issued JWT tokens.

**Acceptance Criteria**:
- `/api/v1/auth/register` creates a user record with password hashed with Argon2id.
- `/api/v1/auth/login` validates credentials and returns a signed JWT access token.
- Password hashing conforms strictly to Argon2 specifications.
- Login failures return generic "Invalid credentials" error messages to prevent account enumeration.

**Prerequisites**:
- Story 1.1 and 1.3 must be completed.

**Context Files to Read**:
- `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Patterns to Follow**:
- Clean Architecture (Auth layer services, DB repositories, API controllers)

**Implementation Steps**:
1. Implement User model in `backend/app/domain/auth.py`.
2. Create authentication logic with Argon2 in `backend/app/services/auth.py`.
3. Set up JWT helper methods to generate tokens.
4. Implement routing handlers under `backend/app/api/auth.py`.

**Test Requirements**:
- Unit tests validating Argon2 hashing.
- Integration tests registering a user, logging in, and verifying the returned token.

**Quality Checks**:
- No hardcoded secret signing keys. Key loaded from environment.

**Out of Scope**:
- User password recovery flows, OAuth registration.

**Completion Evidence**:
- Pytest run output for `backend/tests/api/test_auth.py` passing cleanly.
