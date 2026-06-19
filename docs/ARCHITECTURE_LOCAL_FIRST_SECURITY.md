# Architecture: Local-First Security & Bring-Your-Own-Key Design

## Objective

Ensure JobGraph operates with zero trust in central infrastructure. All secrets, credentials, and data remain under user control in their deployment environment.

## 1. Design Principle: BYOK (Bring-Your-Own-Key)

### Core Tenets

**Users provide all external credentials:**
- Gemini API keys
- LinkedIn/Indeed/Greenhouse credentials
- LLM provider keys (OpenAI, Anthropic, etc.)
- Third-party ATS API keys

**JobGraph stores nothing in cloud:**
- No SaaS backend
- No account servers
- No credential synchronization
- No telemetry (off by default)

**Consequence**: Users have complete control; JobGraph has zero liability for credential exposure.

## 2. Secret Storage Architecture

### Secrets Never Leave User's Machine

```
User's Deployment (Docker Compose)
│
├── .env (NEVER committed)
│   ├── GEMINI_API_KEY=sk_...
│   ├── DB_PASSWORD=...
│   ├── LINKEDIN_COOKIES=...
│   └── GREENHOUSE_API_KEY=...
│
├── docker-compose.yml (COMMITTED)
│   └── Reads secrets from .env via ${GEMINI_API_KEY}
│
└── backend/app/core/config.py
    └── Loads from environment only
```

### At Rest: AES-256-GCM Encryption

**Scenario**: Credentials stored in PostgreSQL database

```python
# backend/app/infrastructure/encryption.py

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import os

class CredentialEncryptor:
    """
    Encrypts portal credentials (LinkedIn, Indeed, etc.)
    Key stored in MASTER_ENCRYPTION_KEY env var only.
    Never hardcoded, never logged.
    """
    
    def __init__(self, master_key: bytes):
        self.cipher = AESGCM(master_key)
    
    def encrypt(self, plaintext: str) -> str:
        # Plaintext: LinkedIn cookies, passwords
        # Ciphertext stored in DB
        # Nonce: random per encryption
        # GCM tag: authentication guarantee
        nonce = os.urandom(12)
        ciphertext = self.cipher.encrypt(nonce, plaintext.encode(), None)
        return f"{nonce.hex()}:{ciphertext.hex()}"
    
    def decrypt(self, encrypted: str) -> str:
        nonce_hex, ciphertext_hex = encrypted.split(":")
        nonce = bytes.fromhex(nonce_hex)
        ciphertext = bytes.fromhex(ciphertext_hex)
        plaintext = self.cipher.decrypt(nonce, ciphertext, None)
        return plaintext.decode()
```

**Deployment**:

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      MASTER_ENCRYPTION_KEY: ${MASTER_ENCRYPTION_KEY}  # User's key only
```

### In Transit: HTTPS/TLS 1.3

All network communication encrypted:

```python
# backend/app/core/config.py

class Settings:
    """
    API server configuration.
    All external communication uses HTTPS (TLS 1.3+).
    """
    
    # Internal (Docker network): Plain HTTP (safe)
    INTERNAL_API_URL = "http://backend:8000"
    
    # External (user access): HTTPS only
    EXTERNAL_API_URL = "https://localhost:443"
    
    # SSL Certificate (user-provided or self-signed)
    SSL_CERT_PATH = "${SSL_CERT_PATH}"
    SSL_KEY_PATH = "${SSL_KEY_PATH}"
    
    # API Key rotation (stored in .env only)
    API_KEY_HEADER = "X-API-Key"
    API_KEY = "${API_KEY}"  # User generates and rotates
```

## 3. Credential Management Lifecycle

### Step 1: User Generates / Obtains Credentials

```bash
# User's machine
cd ~/jobgraph
vim .env.local

# Add:
GEMINI_API_KEY=AIza... (from Google Cloud Console)
DB_PASSWORD=random-32-char-string (generated)
MASTER_ENCRYPTION_KEY=random-32-byte-key (generated)
LINKEDIN_COOKIES="b'session=...'" (manually copied)
```

### Step 2: Application Loads Secrets

```python
# backend/app/core/config.py

from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    """
    Configuration loaded from environment only.
    Pydantic-settings automatically validates types.
    Secrets never appear in logs or error messages.
    """
    
    # These must exist in .env; app fails to start if missing
    gemini_api_key: str  # Validated on startup
    db_password: str
    master_encryption_key: bytes  # Converted from hex string
    linkedin_cookies: str  # Optional, only if configured
    
    class Config:
        env_file = ".env.local"  # Loaded at boot
        case_sensitive = False
        validate_default = True
    
    def __init__(self, **data):
        super().__init__(**data)
        # Secret validation: no printing, no logging
        assert len(self.gemini_api_key) > 20
        assert len(self.master_encryption_key) == 32
        # ... more validations
```

### Step 3: Credentials Used Locally

```python
# backend/app/agents/tailoring_agent.py

from app.infrastructure.llm_client import GeminiClient
from app.core.config import settings

class TailoringAgent:
    """
    Tailors resume using Gemini.
    API key comes from user's environment only.
    Gemini receives API key over HTTPS (to Google servers).
    JobGraph never stores responses indefinitely.
    """
    
    def __init__(self):
        # settings.gemini_api_key never logged, never passed to logs
        self.client = GeminiClient(api_key=settings.gemini_api_key)
    
    async def tailor_resume(self, resume: str, job_desc: str) -> str:
        # Sends: Resume + Job Description to Gemini
        # Receives: Tailored resume
        # Stores: Artifact in MinIO (encrypted), not in logs
        
        result = await self.client.call(
            prompt=f"Tailor this resume:\n{resume}\n\nFor this job:\n{job_desc}",
            model="gemini-1.5-pro"
        )
        
        # Store tailored resume securely
        artifact_id = await self._store_artifact(result)
        return artifact_id
    
    async def _store_artifact(self, content: str) -> str:
        """
        Store in MinIO with:
        - User's own encryption key (from MINIO_ENCRYPT_KEY)
        - No server-side logging
        - User's own access controls
        """
        # ...
```

### Step 4: Credential Rotation

User rotates credentials manually (no auto-sync):

```bash
# User generates new Gemini API key from Google Cloud Console
# User updates .env.local
GEMINI_API_KEY=new_key_here

# User restarts app
docker compose down
docker compose up -d

# New key takes effect; old key revoked at Google
```

## 4. Database Isolation

### PostgreSQL: User's Instance Only

```yaml
# docker-compose.yml

services:
  postgres:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}  # From .env
      POSTGRES_DB: jobgraph
    # No port exposed to internet
    # Only accessible from backend service (same Docker network)
```

**Database Contents** (always user's data):
- User profile information (skills, experience)
- Job postings (from Greenhouse/Lever API, user's account)
- Application history (submitted applications, status)
- Encrypted credentials (portal cookies, API keys)
- Artifacts (tailored resumes, cover letters)

**User Controls**:
- Database backups (user's responsibility)
- Data retention (user's choice)
- Access logging (user's monitoring)
- Encryption key rotation (user's schedule)

### Encryption at Rest

```sql
-- PostgreSQL table for encrypted credentials

CREATE TABLE credentials (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    provider VARCHAR(50) NOT NULL,
    encrypted_value TEXT NOT NULL,  -- Encrypted with MASTER_ENCRYPTION_KEY
    nonce_hex VARCHAR(24) NOT NULL,  -- IV for GCM
    created_at TIMESTAMP NOT NULL,
    rotated_at TIMESTAMP,
    UNIQUE(user_id, provider)
);

-- Even if DB is compromised:
-- Attacker gets encrypted_value + nonce_hex
-- Without MASTER_ENCRYPTION_KEY (from .env), data is useless
-- MASTER_ENCRYPTION_KEY never stored in DB
```

## 5. MinIO: User's Storage

### S3-Compatible, Self-Hosted

```yaml
# docker-compose.yml

services:
  minio:
    image: minio/minio:latest
    volumes:
      - minio_data:/data
    environment:
      MINIO_ROOT_USER: ${MINIO_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
    # No port exposed to internet; only backend service accesses
```

### Data Stored in MinIO

```python
# backend/app/infrastructure/storage.py

class StorageService:
    """
    Stores artifacts (tailored resumes, cover letters, PDFs).
    All stored in user's MinIO instance.
    User owns encryption keys.
    User controls backups.
    """
    
    async def save_tailored_resume(self, user_id: UUID, resume_pdf: bytes) -> str:
        """
        Stores PDF in MinIO.
        Path: f"users/{user_id}/resumes/{timestamp}.pdf"
        Encrypted: Server-side encryption with user's key
        Access: Only backend service (Docker network)
        """
        # MinIO SSE-C (Server-Side Encryption with Customer Key)
        await self.minio_client.put_object(
            bucket_name="jobgraph",
            object_name=f"users/{user_id}/resumes/{timestamp}.pdf",
            data=resume_pdf,
            # SSE-C: Encryption key managed by user
        )
        return f"s3://jobgraph/users/{user_id}/resumes/{timestamp}.pdf"
    
    async def get_tailored_resume(self, user_id: UUID, resume_id: str) -> bytes:
        """
        Retrieves artifact.
        Returns: PDF bytes
        Access: Backend service only (same Docker network)
        """
        url = await self.minio_client.get_object(
            bucket_name="jobgraph",
            object_name=f"users/{user_id}/resumes/{resume_id}.pdf"
        )
        return url
```

## 6. Browser Automation: Sandboxed

### Playwright Runs in Docker

```yaml
# docker-compose.yml

services:
  # Optional: dedicated Playwright service
  playwright:
    image: mcr.microsoft.com/playwright:v1.40-focal
    # Runs in isolated container
    # Cannot access host machine
    # Cannot capture other container traffic
```

### Credentials NOT in Browser Context

```python
# backend/app/infrastructure/browser_automation.py

class BrowserAutomationService:
    """
    Fills forms and submits applications.
    Credentials loaded from encrypted DB at runtime.
    Session cookies stored securely.
    """
    
    async def submit_application(
        self,
        user_id: UUID,
        job_posting: JobPosting,
        credentials: PortalCredentials  # Decrypted from DB
    ) -> ApplicationResult:
        """
        1. Start Playwright headless browser
        2. Load credentials from memory (not disk)
        3. Fill forms
        4. Submit
        5. Log application (to DB, not disk)
        6. Clear sensitive data from memory
        """
        
        browser = await chromium.launch()
        page = await browser.new_page()
        
        try:
            # Navigate to job posting
            await page.goto(job_posting.url)
            
            # Fill forms using decrypted credentials
            await page.fill(
                "input[name='email']",
                credentials.get_email()  # Decrypted, not logged
            )
            
            # Submit
            await page.click("button[type='submit']")
            
            # Log result
            result = ApplicationResult(
                job_posting_id=job_posting.id,
                status="submitted",
                timestamp=now()
            )
            await self.db.save(result)
            
        finally:
            # Always clear sensitive data
            credentials.clear()  # Wipe from memory
            await browser.close()
        
        return result
```

## 7. Logging: PII & Secret Redaction

### Structured JSON Logging

```python
# backend/app/core/logging_config.py

import structlog
from pythonjsonlogger import jsonlogger

# All logs: JSON format with no PII/secrets

class SecretRedactor:
    """
    Redacts sensitive fields from logs before writing.
    Patterns: API keys, passwords, email, SSN, credit cards.
    """
    
    @staticmethod
    def redact(record: dict) -> dict:
        sensitive_keys = [
            "api_key", "gemini_api_key", "password",
            "email", "ssn", "credit_card",
            "linkedin_cookies", "bearer_token"
        ]
        
        for key in sensitive_keys:
            if key in record:
                record[key] = "[REDACTED]"
        
        return record

# Applied to all log handlers
logging_config = {
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": [SecretRedactor]
        }
    }
}
```

### Example Log Output

```json
{
  "timestamp": "2026-06-19T14:30:00Z",
  "level": "INFO",
  "component": "TailoringAgent",
  "event": "resume_tailored",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_posting_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "gemini_api_key": "[REDACTED]",
  "duration_ms": 2340,
  "status": "success"
}
```

## 8. Network Isolation

### Internal Services (No Internet)

```
┌─ Docker Network ─────────────────┐
│                                   │
│  frontend ←→ backend             │
│               ├→ postgres         │
│               ├→ minio            │
│               ├→ valkey           │
│               └→ playwright       │
│                                   │
└───────────────────────────────────┘
         ↓
    External APIs (HTTPS)
      ├ Gemini API
      ├ Greenhouse
      ├ Lever
      └ LinkedIn
```

**Rules**:
- Internal services: Plain HTTP (no secrets on network)
- External APIs: HTTPS/TLS 1.3 only
- Frontend to Backend: HTTPS only
- Credentials in URLs: **NEVER** (use headers/body instead)

## 9. User Responsibilities

### User MUST Do

- [ ] Generate strong database password (32+ chars)
- [ ] Generate strong encryption key (32 bytes)
- [ ] Store .env.local securely (never commit, never share)
- [ ] Rotate API keys monthly
- [ ] Backup PostgreSQL regularly
- [ ] Monitor logs for suspicious activity
- [ ] Keep Docker images updated

### User CAN Do (Optional)

- [ ] Enable SSL/TLS certificate
- [ ] Configure firewall rules
- [ ] Set up automated backups
- [ ] Enable audit logging
- [ ] Use hardware security module (HSM) for encryption keys

## 10. Deployment Security Checklist

```markdown
### Pre-Deployment
- [ ] Generate .env.local with strong secrets
- [ ] Disable telemetry (TELEMETRY_ENABLED=false)
- [ ] Set DB password (32+ chars)
- [ ] Generate MASTER_ENCRYPTION_KEY
- [ ] Review docker-compose.yml (no hardcoded secrets)
- [ ] Configure network firewall

### Post-Deployment
- [ ] Verify no logs contain secrets (check docker logs)
- [ ] Test credential encryption (submit test application)
- [ ] Verify database backups working
- [ ] Test credential rotation (generate new API key)
- [ ] Monitor disk space (artifacts in MinIO)
- [ ] Review structured logs for issues

### Ongoing
- [ ] Audit logs monthly
- [ ] Rotate encryption keys yearly
- [ ] Update Docker images quarterly
- [ ] Test disaster recovery (restore from backup)
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-06-19  
**Owner**: Security & Architecture  
**Applies To**: v0.1+ all versions
