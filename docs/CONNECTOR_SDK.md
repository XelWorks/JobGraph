# Connector SDK Guide

## Overview

JobGraph provides a plugin architecture for adding support for new ATS platforms (Greenhouse, Lever, Workable, etc.).

This guide shows how to:
1. Understand the connector interface
2. Implement a custom connector
3. Register and test locally
4. Contribute back to the project

## Architecture

### Connector Registry Pattern

```
ConnectorRegistry
├── greenhouse (built-in)
├── lever (built-in)
├── workable (built-in)
└── custom (user-provided)
```

All connectors implement the same interface, allowing job discovery and application from any ATS.

## Connector Interface

All connectors inherit from `BaseConnector`:

```python
# backend/app/infrastructure/connectors/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass
class JobPosting:
    """Normalized job posting from any ATS."""
    id: str  # Provider's job ID
    provider: str  # "greenhouse", "lever", "workable"
    title: str
    description: str
    company: str
    location: str
    url: str  # Application URL
    posted_date: datetime
    metadata: dict  # Provider-specific fields

@dataclass
class ApplicationResult:
    """Result of submitting an application."""
    job_posting_id: str
    status: str  # "submitted", "failed", "pending_verification"
    message: str  # "Application submitted successfully" or error
    timestamp: datetime
    artifact_ids: list[str]  # Tailored resume IDs, etc.

class BaseConnector(ABC):
    """
    Abstract base for all ATS connectors.
    Subclass this to add support for a new ATS.
    """
    
    provider_name: str  # "workable", "icims", etc.
    
    def __init__(self, credentials: dict):
        """
        Initialize connector with user credentials.
        
        Args:
            credentials: Dict with provider-specific auth
                {
                    "api_key": "...",
                    "portal_cookies": "...",
                    "email": "user@example.com"
                }
        """
        self.credentials = credentials
    
    @abstractmethod
    async def get_jobs(
        self,
        search_query: str = None,
        filters: dict = None
    ) -> list[JobPosting]:
        """
        Fetch job postings from ATS.
        
        Args:
            search_query: Keywords to search for ("Python developer", etc.)
            filters: Optional filtering ({
                "location": "New York",
                "salary_min": 100000,
                "job_type": "full_time"
            })
        
        Returns:
            List of JobPosting objects
        
        Example:
            jobs = await connector.get_jobs("Python engineer", {"location": "SF"})
        """
        pass
    
    @abstractmethod
    async def apply(
        self,
        job_posting: JobPosting,
        application_data: dict
    ) -> ApplicationResult:
        """
        Submit an application for a job posting.
        
        Args:
            job_posting: JobPosting object (from get_jobs)
            application_data: User's application info {
                "resume_url": "s3://...resume.pdf",
                "cover_letter": "Dear hiring manager...",
                "custom_answers": {
                    "What's your experience?": "5 years..."
                }
            }
        
        Returns:
            ApplicationResult with submission status
        
        Example:
            result = await connector.apply(job, {
                "resume_url": "s3://...",
                "cover_letter": "..."
            })
        """
        pass
    
    async def validate_credentials(self) -> bool:
        """
        Test if credentials are valid.
        Called when user first connects an ATS.
        
        Returns:
            True if valid, False otherwise
        
        Example:
            if await connector.validate_credentials():
                print("Connected to Workable successfully")
        """
        pass
```

## Building a Custom Connector

### Example: Workable ATS Connector

```python
# backend/app/infrastructure/connectors/workable.py

import httpx
from typing import Optional
from app.infrastructure.connectors.base import BaseConnector, JobPosting, ApplicationResult

class WorkableConnector(BaseConnector):
    provider_name = "workable"
    API_BASE = "https://www.workable.com/api/v1"
    
    async def get_jobs(
        self,
        search_query: Optional[str] = None,
        filters: Optional[dict] = None
    ) -> list[JobPosting]:
        """
        Fetch jobs from Workable job board.
        """
        api_key = self.credentials.get("api_key")
        if not api_key:
            raise ValueError("Workable API key required")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
        
        params = {}
        if search_query:
            params["query"] = search_query
        if filters:
            if "location" in filters:
                params["location"] = filters["location"]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE}/jobs",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            jobs_data = response.json()
            
            # Transform Workable API response to JobPosting objects
            jobs = []
            for job_data in jobs_data.get("jobs", []):
                job = JobPosting(
                    id=job_data["id"],
                    provider="workable",
                    title=job_data["title"],
                    description=job_data["description"],
                    company=job_data["company"],
                    location=job_data["location"],
                    url=job_data["application_url"],
                    posted_date=job_data["created_at"],
                    metadata={
                        "job_type": job_data.get("job_type"),
                        "salary": job_data.get("salary"),
                        "department": job_data.get("department")
                    }
                )
                jobs.append(job)
            
            return jobs
    
    async def apply(
        self,
        job_posting: JobPosting,
        application_data: dict
    ) -> ApplicationResult:
        """
        Submit application via Workable.
        """
        # Download resume from S3
        resume_url = application_data["resume_url"]
        resume_bytes = await self._download_file(resume_url)
        
        # Prepare form data
        files = {
            "resume": ("resume.pdf", resume_bytes, "application/pdf")
        }
        form_data = {
            "email": self.credentials["email"],
            "name": application_data.get("name", ""),
            "phone": application_data.get("phone", ""),
            "cover_letter": application_data.get("cover_letter", "")
        }
        
        # Add custom answers
        for key, value in application_data.get("custom_answers", {}).items():
            form_data[f"custom_{key}"] = value
        
        # Submit application
        async with httpx.AsyncClient() as client:
            response = await client.post(
                job_posting.url,
                data=form_data,
                files=files
            )
        
        if response.status_code in (200, 201, 302):
            return ApplicationResult(
                job_posting_id=job_posting.id,
                status="submitted",
                message="Application submitted successfully",
                timestamp=datetime.now(),
                artifact_ids=[resume_url]
            )
        else:
            return ApplicationResult(
                job_posting_id=job_posting.id,
                status="failed",
                message=f"HTTP {response.status_code}: {response.text}",
                timestamp=datetime.now(),
                artifact_ids=[]
            )
    
    async def validate_credentials(self) -> bool:
        """Test API key validity."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.API_BASE}/profile",
                    headers={
                        "Authorization": f"Bearer {self.credentials['api_key']}"
                    }
                )
                return response.status_code == 200
        except Exception:
            return False
    
    async def _download_file(self, url: str) -> bytes:
        """Helper: download file from URL."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
```

## Registration

Register your connector in the connector registry:

```python
# backend/app/infrastructure/connectors/__init__.py

from app.infrastructure.connectors.base import BaseConnector
from app.infrastructure.connectors.greenhouse import GreenhouseConnector
from app.infrastructure.connectors.lever import LeverConnector
from app.infrastructure.connectors.workable import WorkableConnector  # New

class ConnectorRegistry:
    _connectors = {}
    
    @classmethod
    def register(cls, name: str, connector_class: type):
        """Register a connector."""
        cls._connectors[name] = connector_class
    
    @classmethod
    def get(cls, name: str) -> type:
        """Get connector class by name."""
        if name not in cls._connectors:
            raise ValueError(f"Unknown connector: {name}")
        return cls._connectors[name]
    
    @classmethod
    def list_available(cls) -> list[str]:
        """List all registered connectors."""
        return list(cls._connectors.keys())

# Register built-in connectors
ConnectorRegistry.register("greenhouse", GreenhouseConnector)
ConnectorRegistry.register("lever", LeverConnector)
ConnectorRegistry.register("workable", WorkableConnector)  # NEW
```

## Testing Your Connector

### Unit Tests

```python
# backend/tests/infrastructure/connectors/test_workable.py

import pytest
from unittest.mock import AsyncMock, patch
from app.infrastructure.connectors.workable import WorkableConnector
from app.infrastructure.connectors.base import JobPosting

@pytest.fixture
def connector():
    credentials = {
        "api_key": "test_key_123",
        "email": "user@example.com"
    }
    return WorkableConnector(credentials)

@pytest.mark.asyncio
async def test_get_jobs(connector):
    """Test fetching jobs from Workable."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "jobs": [
                {
                    "id": "job_123",
                    "title": "Python Engineer",
                    "description": "Build web apps...",
                    "company": "TechCorp",
                    "location": "New York",
                    "application_url": "https://...",
                    "created_at": "2026-06-19T00:00:00Z",
                    "job_type": "full_time"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        jobs = await connector.get_jobs("Python")
        
        assert len(jobs) == 1
        assert jobs[0].title == "Python Engineer"
        assert jobs[0].provider == "workable"

@pytest.mark.asyncio
async def test_validate_credentials(connector):
    """Test credential validation."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        is_valid = await connector.validate_credentials()
        
        assert is_valid is True
```

### Integration Tests

```python
# backend/tests/infrastructure/connectors/test_workable_integration.py

import pytest
from app.infrastructure.connectors.workable import WorkableConnector

# Test with real API (optional, requires test account)
# Set WORKABLE_API_KEY env var to enable

@pytest.mark.skipif(
    not os.getenv("WORKABLE_API_KEY"),
    reason="WORKABLE_API_KEY not set"
)
@pytest.mark.asyncio
async def test_real_api():
    connector = WorkableConnector({
        "api_key": os.getenv("WORKABLE_API_KEY"),
        "email": "test@example.com"
    })
    
    # Test real API call
    jobs = await connector.get_jobs("Python")
    assert len(jobs) > 0
    assert jobs[0].provider == "workable"
```

### Run Tests

```bash
# Unit tests only
pytest backend/tests/infrastructure/connectors/test_workable.py

# With integration tests (if real API available)
WORKABLE_API_KEY=... pytest backend/tests/infrastructure/connectors/test_workable_integration.py -v

# Check coverage
pytest backend/tests/infrastructure/connectors/ --cov=app.infrastructure.connectors --cov-report=html
```

## Submission Checklist

Before submitting a new connector:

- [ ] Implements all methods from `BaseConnector`
- [ ] Has ≥85% test coverage
- [ ] Passes all unit and integration tests
- [ ] Handles errors gracefully (timeouts, rate limits, 404s)
- [ ] Logs errors with structured JSON
- [ ] Never logs credentials or sensitive data
- [ ] Respects ATS API rate limits
- [ ] Has documentation (README.md in connector folder)
- [ ] Follows coding standards (Black, Pylint, Mypy)
- [ ] Includes example usage in docstrings

## Contributing a Connector

1. **Fork the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/jobgraph.git
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/workable-connector
   ```

3. **Implement the connector** (see example above)

4. **Add tests** (see Testing section)

5. **Update documentation**
   ```markdown
   # docs/connectors/workable.md
   
   ## Workable ATS Connector
   
   ### Setup
   1. Get API key from Workable admin panel
   2. Add to configuration:
      - WORKABLE_API_KEY=...
      - WORKABLE_ACCOUNT=company-name
   
   ### Supported Features
   - Job search by keyword
   - Job filtering by location
   - Application submission
   - Resume upload
   ```

6. **Submit PR**
   ```bash
   git push origin feature/workable-connector
   # Create PR on GitHub
   ```

7. **Community Review**
   - Core team reviews code
   - Tests must pass
   - Coverage must be ≥85%
   - PR approved and merged

## API Reference

### JobPosting

```python
@dataclass
class JobPosting:
    id: str                    # Provider's job ID
    provider: str              # "greenhouse", "lever", "workable"
    title: str                 # Job title
    description: str           # Full job description
    company: str               # Company name
    location: str              # Job location
    url: str                   # Application URL
    posted_date: datetime      # When posted
    metadata: dict             # Provider-specific fields
```

### ApplicationResult

```python
@dataclass
class ApplicationResult:
    job_posting_id: str        # ID of job applied for
    status: str                # "submitted", "failed", "pending"
    message: str               # Success or error message
    timestamp: datetime        # When application was submitted
    artifact_ids: list[str]    # S3 URLs of attachments (resume, etc.)
```

## Troubleshooting

### Issue: "Unknown connector"
```python
# Make sure connector is registered
ConnectorRegistry.register("my_connector", MyConnector)

# Verify
ConnectorRegistry.list_available()  # Should include "my_connector"
```

### Issue: Credentials validation fails
```python
# Check that API key format is correct for provider
# Test with real credentials in development

# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Issue: Rate limiting / 429 errors
```python
# Implement exponential backoff
import asyncio

async def get_jobs_with_retry(self):
    for attempt in range(3):
        try:
            return await self.get_jobs()
        except RateLimitError:
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            await asyncio.sleep(wait_time)
    raise Exception("Rate limit exceeded after 3 attempts")
```

## Support

- **Questions**: Open a GitHub Discussion
- **Issues**: Report on GitHub Issues
- **SDK Help**: docs/CONNECTOR_SDK.md
- **Examples**: github.com/jobgraph/jobgraph-connectors (coming soon)

---

**Version**: 1.0  
**Last Updated**: 2026-06-19
