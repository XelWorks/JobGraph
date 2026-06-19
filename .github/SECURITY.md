# Security Policy

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.** Instead, please report security issues privately to: **security@jobgraph.dev**

Include:

1. **Description**: What is the vulnerability?
2. **Location**: File path, function name, version affected
3. **Proof of Concept**: Steps to reproduce (if safe to share)
4. **Impact**: What can an attacker do?
5. **Suggested Fix**: If known (optional)

We will:

- Acknowledge receipt within 48 hours
- Provide a timeline for fix and release
- Credit you in security advisory (if desired)
- Coordinate responsible disclosure

## Security Expectations

### What We Commit To

- Promptly review all reported security issues
- Release security patches for latest stable version
- Maintain backward-compatible fixes when possible
- Publish security advisories on GitHub

### What We Don't Cover

- Vulnerabilities in third-party dependencies (report to upstream maintainers)
- Configuration issues (e.g., exposed credentials in user's deployment)
- Denial of Service from legitimate heavy usage

### Security Best Practices for Users

1. **Keep JobGraph Updated**
   ```bash
   git pull origin main
   docker compose pull
   docker compose up -d
   ```

2. **Manage Credentials Securely**
   - Store API keys in `.env.local` (never commit)
   - Rotate keys regularly
   - Use strong database passwords
   - Enable database encryption at rest

3. **Network Security**
   - Run JobGraph behind a VPN or firewall
   - Use HTTPS for external access
   - Restrict database access to application container

4. **Audit Logging**
   - Enable structured JSON logging (default in production)
   - Monitor logs for suspicious activity
   - Review application audit trail regularly

## Supported Versions

| Version | Supported Until |
|---------|-----------------|
| 0.1.x (MVP) | Until 0.2 released |
| 0.2.x | 6 months after 1.0 release |
| 1.0+ | Latest + 2 prior minor versions |

## Security Headers & Configuration

When deploying JobGraph:

1. **Database**
   ```yaml
   # docker-compose.yml
   postgresql:
     environment:
       POSTGRES_PASSWORD: ${DB_PASSWORD}  # Strong, 32+ char random
     volumes:
       - postgresql_data:/var/lib/postgresql/data
   ```

2. **API**
   ```python
   # backend/app/core/config.py
   CORS_ORIGINS = ["https://your-domain.com"]  # Restrict to your origin
   ALLOW_CREDENTIALS = True
   API_KEY_HEADER = "X-API-Key"  # Rotate regularly
   ```

3. **Secrets Management**
   - Use Docker secrets for production deployments
   - Never log API keys or passwords
   - Rotate credentials monthly

## Vulnerability Disclosure Timeline

After you report a vulnerability:

1. **Days 1-2**: Acknowledgment and initial assessment
2. **Days 3-7**: Security patch development and testing
3. **Day 7**: Security advisory published
4. **Day 14**: Public disclosure (if patch available)

For critical vulnerabilities, timeline may be accelerated.

## Attribution

Security researchers who responsibly disclose vulnerabilities will be:

- Credited in security advisory (name/handle/website)
- Notified before public disclosure
- Given opportunity to verify fix before release

Thank you for helping keep JobGraph secure!
