# AutoApply AI - Autonomous Job Application System

## Overview

This system works autonomously on your behalf to discover jobs, tailor your resume, and apply to positions even when you're away from your desk.

## Key Features Fixed & Implemented

### 1. **Autonomous Scheduler** (`/backend/app/services/autonomous/scheduler.py`)
- ✅ Continuous background job discovery from LinkedIn, Naukri, Glassdoor
- ✅ Automated resume tailoring for each job using AI
- ✅ Intelligent application scheduling with configurable rate limits
- ✅ Daily application limits (default: 50 applications/day)
- ✅ Session management and automatic refresh
- ✅ Retry logic with exponential backoff (max 3 retries)
- ✅ Duplicate application prevention
- ✅ Daily progress tracking

### 2. **Security Enhancements** (`/backend/app/core/config.py`)
- ✅ Secure credential generation using `secrets` module
- ✅ Environment variable support for all sensitive keys
- ✅ Automatic generation of secure random keys if not provided
- ✅ Rate limiting per portal to prevent bans:
  - LinkedIn: 60 seconds between requests
  - Naukri: 60 seconds between requests
  - Glassdoor: 60 seconds between requests
  - Greenhouse/Lever: 30 seconds between requests

### 3. **Account Creation on Career Pages** (`/backend/app/services/applications/account_creator.py`)
- ✅ Automatic detection of company career page redirects
- ✅ Support for major ATS platforms:
  - Greenhouse
  - Lever
  - Workday
  - iCIMS
  - Taleo/Oracle
- ✅ Secure password generation (16 characters with mixed case, numbers, symbols)
- ✅ Encrypted credential storage in vault
- ✅ Session cookie capture and reuse
- ✅ Automatic login with stored credentials

### 4. **Enhanced Browser Automation** (`/backend/app/infrastructure/browser/playwright_client.py`)
- ✅ ATS platform detection from URLs
- ✅ Account creation integration when redirected to career pages
- ✅ Improved form filling for all major ATS systems
- ✅ Better error handling and timeout management
- ✅ Manual review pause for CAPTCHA/MFA challenges

### 5. **Application Service Improvements** (`/backend/app/services/applications/application_service.py`)
- ✅ Portal name inference from job URLs
- ✅ Session payload handling for persistent logins
- ✅ Queue-based task dispatch for background processing

### 6. **Browser Worker** (`/workers/browser_worker.py`)
- ✅ Standalone worker process for browser automation
- ✅ Graceful shutdown handling
- ✅ Task polling with configurable intervals
- ✅ Status tracking and event emission
- ✅ Error recovery and continuation

## Configuration

### Environment Variables (`.env`)

```bash
# Security Keys (auto-generated if not provided)
MINIO_PASSWORD=your_secure_minio_password
GEMINI_API_KEY=your_gemini_api_key
MASTER_ENCRYPTION_KEY=your_64_char_hex_key
JWT_SECRET_KEY=your_64_char_hex_key
API_KEY=your_32_char_api_key

# Autonomous Mode Settings
AUTONOMOUS_MODE_ENABLED=true
MAX_APPLICATIONS_PER_DAY=50
APPLICATION_INTERVAL_SECONDS=300
JOB_DISCOVERY_INTERVAL_SECONDS=1800
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=60
RATE_LIMIT_DELAY_SECONDS=30
SESSION_REFRESH_INTERVAL_HOURS=12
DAILY_REPORT_ENABLED=true
DAILY_REPORT_HOUR=8

# Per-Portal Rate Limits
LINKEDIN_RATE_LIMIT_SECONDS=60
NAUKRI_RATE_LIMIT_SECONDS=60
GLASSDOOR_RATE_LIMIT_SECONDS=60
GREENHOUSE_RATE_LIMIT_SECONDS=30
LEVER_RATE_LIMIT_SECONDS=30

# Account Creation
AUTO_CREATE_ACCOUNTS=true
DEFAULT_PASSWORD_LENGTH=16
```

## Usage

### Starting the System

1. **Start the backend API server** (includes autonomous scheduler):
```bash
cd /workspace/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The autonomous scheduler starts automatically if `AUTONOMOUS_MODE_ENABLED=true`.

2. **Start the browser worker** (separate process):
```bash
cd /workspace
python workers/browser_worker.py
```

### Manual Application Dispatch

You can also manually trigger applications via API:

```bash
# Apply to a specific job URL
curl -X POST "http://localhost:8000/api/v1/applications/from-link" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_url": "https://www.linkedin.com/jobs/view/123456",
    "mode": "Autonomous",
    "requires_review": false
  }'
```

### Monitoring Applications

```bash
# List all applications
curl "http://localhost:8000/api/v1/applications" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get dashboard metrics
curl "http://localhost:8000/api/v1/applications/metrics" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## How It Works

### Autonomous Flow

1. **Discovery Phase** (every 30 minutes):
   - Scans LinkedIn, Naukri, Glassdoor for new jobs
   - Uses saved browser sessions for authenticated access
   - Filters jobs based on user profile/skills

2. **Tailoring Phase**:
   - Fetches master resume from secure storage
   - Uses Gemini AI to tailor resume for each job
   - Saves tailored resume with unique identifier

3. **Application Phase**:
   - Creates application record in database
   - Dispatches task to browser worker queue
   - Worker opens browser with saved session
   - Detects ATS platform (Greenhouse, Lever, etc.)
   - If career page redirect: creates account automatically
   - Fills application form with profile data
   - Uploads tailored resume
   - Answers custom questions using AI
   - Submits application (or pauses for review if needed)

4. **Tracking Phase**:
   - Updates application status in real-time
   - Emits events for UI updates
   - Stores session cookies for future use
   - Logs success/failure metrics

### Account Creation Flow

When a job link redirects to a company career page:

1. Detect ATS platform from URL pattern
2. Check if already logged in (look for logout button/profile)
3. Check vault for stored credentials
4. If no credentials and auto-create enabled:
   - Navigate to signup page
   - Generate secure 16-character password
   - Fill registration form with profile data
   - Submit and verify account creation
   - Store encrypted credentials in vault
   - Capture session cookies
5. Proceed with application using new account

## Error Handling

### Retry Logic
- Failed applications retry up to 3 times
- Exponential backoff: 60s, 120s, 240s delays
- Different error types trigger different retry strategies

### Rate Limiting
- Per-user daily limits prevent excessive applications
- Per-portal delays prevent IP bans
- Automatic pause when limits reached

### Session Management
- Sessions checked before each application
- Expired sessions trigger re-authentication
- Cookies stored encrypted in vault
- Session refresh every 12 hours

## Security Best Practices

1. **Never commit `.env` file** - Contains sensitive keys
2. **Use strong passwords** - Auto-generated by default
3. **Enable HTTPS** - In production deployments
4. **Regular key rotation** - Change encryption keys periodically
5. **Monitor logs** - Watch for suspicious activity

## Troubleshooting

### Common Issues

**Scheduler not starting:**
- Check `AUTONOMOUS_MODE_ENABLED=true` in `.env`
- Verify user has complete profile with master resume

**Applications failing:**
- Check browser worker is running
- Verify portal sessions are valid
- Review logs for specific error messages

**Account creation failing:**
- Some platforms require email verification
- CAPTCHA may require manual intervention
- Check `AUTO_CREATE_ACCOUNTS=true` in config

**Rate limit errors:**
- Increase `APPLICATION_INTERVAL_SECONDS`
- Reduce `MAX_APPLICATIONS_PER_DAY`
- Check portal-specific rate limits

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   FastAPI App   │────▶│  Valkey Queue    │────▶│ Browser Worker  │
│                 │     │                  │     │                 │
│ - REST API      │     │ - Task Queue     │     │ - Playwright    │
│ - Scheduler     │     │ - Job Dispatch   │     │ - Form Fill     │
│ - Tailoring     │     │                  │     │ - Submit        │
└────────┬────────┘     └──────────────────┘     └────────┬────────┘
         │                                                 │
         ▼                                                 ▼
┌─────────────────┐                              ┌─────────────────┐
│   PostgreSQL    │                              │   Chrome/Browser│
│                 │                              │                 │
│ - Users         │                              │ - Persistent    │
│ - Profiles      │                              │   Sessions      │
│ - Applications  │                              │ - Automation    │
│ - Jobs          │                              │                 │
└─────────────────┘                              └─────────────────┘
```

## License

Proprietary - All rights reserved
