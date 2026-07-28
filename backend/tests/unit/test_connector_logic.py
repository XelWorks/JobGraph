import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select

from app.domain.job import JobPosting
from app.infrastructure.db.session import SessionLocal
from app.services.discovery.connector import GreenhouseConnector, LeverConnector

# --- MOCK RAW PAYLOADS ---

MOCK_GREENHOUSE_RAW = {
    "id": 12345,
    "title": "Staff Platform Engineer ",
    "absolute_url": "https://boards.greenhouse.io/mockcompany/jobs/12345",
    "location": {"name": "Remote, US"},
    "content": "<h1>Job Description Details</h1>"
}

MOCK_LEVER_RAW = {
    "id": "lever-uuid-9876",
    "text": "Senior generative AI Developer ",
    "hostedUrl": "https://jobs.lever.co/mockcomp/lever-uuid-9876",
    "categories": {"location": "Austin, TX"},
    "descriptionPlain": "Full-time position creating agents.",
    "lists": [
        {
            "text": "Required Qualifications",
            "content": ["3+ years Python", "LangGraph workflows"]
        }
    ]
}

# --- TESTS ---

def test_greenhouse_connector_parse():
    """Verify Greenhouse parsing normalizes titles, external IDs, and formats."""
    connector = GreenhouseConnector()
    parsed = connector.parse_job(MOCK_GREENHOUSE_RAW, "mockcompany")
    
    assert parsed["external_job_id"] == "12345"
    assert parsed["title"] == "Staff Platform Engineer"  # Trimmed whitespace
    assert parsed["company"] == "Mockcompany"
    assert parsed["location"] == "Remote, US"
    assert parsed["url"] == "https://boards.greenhouse.io/mockcompany/jobs/12345"
    assert parsed["description_text"] == "<h1>Job Description Details</h1>"

def test_lever_connector_parse():
    """Verify Lever parsing handles categorized sections and bullet listings."""
    connector = LeverConnector()
    parsed = connector.parse_job(MOCK_LEVER_RAW, "mockcomp")
    
    assert parsed["external_job_id"] == "lever-uuid-9876"
    assert parsed["title"] == "Senior generative AI Developer"
    assert parsed["company"] == "Mockcomp"
    assert parsed["location"] == "Austin, TX"
    assert "Required Qualifications:" in parsed["description_text"]
    assert "- LangGraph workflows" in parsed["description_text"]

@pytest.mark.asyncio
async def test_connector_sync_deduplication():
    """Verify connectors dynamically insert records and skip existing listings to guarantee deduplication."""
    # Build clean test records using NullPool postgres context
    async with SessionLocal() as session:
        board_token = "mockcompany-test"
        connector = GreenhouseConnector()
        
        # Patch fetch_jobs to yield our mock greenhouse listings
        with patch.object(GreenhouseConnector, "fetch_jobs", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [MOCK_GREENHOUSE_RAW]
            
            # Sync first time (inserts the record)
            synced_first = await connector.sync_board(session, board_token)
            assert len(synced_first) == 1
            record_id = synced_first[0].id
            
            # Re-sync to verify deduplication behavior
            synced_second = await connector.sync_board(session, board_token)
            assert len(synced_second) == 1
            assert synced_second[0].id == record_id  # Returns the same database primary key ID
            
            # Assert query returns exactly one record in the database, validating deduplication
            query = select(JobPosting).where(
                JobPosting.platform == "Greenhouse",
                JobPosting.external_job_id == "12345",
                JobPosting.board_token == board_token
            )
            res = await session.execute(query)
            listings = res.scalars().all()
            assert len(listings) == 1
            
            # Cleanup Database listing record
            await session.delete(listings[0])
            await session.commit()
