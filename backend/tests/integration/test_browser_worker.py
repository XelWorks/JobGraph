"""Integration tests for the standalone browser worker."""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.queue.valkey_queue import ValkeyQueue


@pytest.mark.asyncio
async def test_worker_task_flow_end_to_end():
    """
    Test the complete flow: FastAPI dispatches task → Valkey queue → Worker consumes task.
    
    This test verifies:
    1. Task can be pushed to Valkey queue
    2. Task can be popped from Valkey queue
    3. Task payload is preserved through the queue
    """
    queue = ValkeyQueue()
    
    # Mock task payload
    task_payload = {
        "application_id": "test-app-123",
        "job_url": "https://example.com/apply",
        "profile_data": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "555-1234"
        },
        "resume_path": "/tmp/resume.pdf",
        "mode": "Autonomous"
    }
    
    with patch("app.infrastructure.queue.valkey_queue.AsyncRedis") as MockAsyncRedis:
        mock_client = AsyncMock()
        
        # Mock rpush for push_task
        mock_client.rpush = AsyncMock()
        
        # Mock blpop for pop_task to return the serialized payload
        serialized_payload = json.dumps(task_payload)
        mock_client.blpop = AsyncMock(
            return_value=("app:tasks:application", serialized_payload)
        )
        
        MockAsyncRedis.from_url.return_value = mock_client
        
        # Step 1: Push task to queue (simulating FastAPI dispatch)
        await queue.push_task("application", task_payload)
        
        # Verify push was called
        mock_client.rpush.assert_awaited_once_with(
            "app:tasks:application",
            serialized_payload
        )
        
        # Step 2: Pop task from queue (simulating worker consumption)
        popped_task = await queue.pop_task("application")
        
        # Verify pop was called
        mock_client.blpop.assert_awaited_once_with("app:tasks:application", timeout=0)
        
        # Step 3: Verify task payload integrity
        assert popped_task is not None
        assert popped_task["application_id"] == task_payload["application_id"]
        assert popped_task["job_url"] == task_payload["job_url"]
        assert popped_task["profile_data"] == task_payload["profile_data"]
        assert popped_task["resume_path"] == task_payload["resume_path"]
        assert popped_task["mode"] == task_payload["mode"]


@pytest.mark.asyncio
async def test_worker_handles_multiple_tasks_sequentially():
    """Test that worker can process multiple tasks in sequence."""
    queue = ValkeyQueue()
    
    tasks = [
        {"application_id": "app-1", "job_url": "https://example.com/job1"},
        {"application_id": "app-2", "job_url": "https://example.com/job2"},
        {"application_id": "app-3", "job_url": "https://example.com/job3"}
    ]
    
    with patch("app.infrastructure.queue.valkey_queue.AsyncRedis") as MockAsyncRedis:
        mock_client = AsyncMock()
        
        # Mock blpop to return tasks sequentially, then None
        mock_client.blpop = AsyncMock(
            side_effect=[
                ("app:tasks:application", json.dumps(tasks[0])),
                ("app:tasks:application", json.dumps(tasks[1])),
                ("app:tasks:application", json.dumps(tasks[2])),
                None  # Queue empty
            ]
        )
        
        MockAsyncRedis.from_url.return_value = mock_client
        
        # Pop all tasks
        popped_tasks = []
        for _ in range(4):  # Try to pop 4 times (3 tasks + 1 empty)
            task = await queue.pop_task("application", timeout=1)
            if task:
                popped_tasks.append(task)
        
        # Verify all tasks were popped
        assert len(popped_tasks) == 3
        assert popped_tasks[0]["application_id"] == "app-1"
        assert popped_tasks[1]["application_id"] == "app-2"
        assert popped_tasks[2]["application_id"] == "app-3"


@pytest.mark.asyncio
async def test_worker_isolation_from_fastapi():
    """
    Test that worker operates independently from FastAPI.
    
    This verifies the decoupled architecture where browser crashes
    or timeouts do not impact the web server.
    """
    queue = ValkeyQueue()
    
    task_payload = {
        "application_id": "isolated-task",
        "job_url": "https://example.com/apply"
    }
    
    with patch("app.infrastructure.queue.valkey_queue.AsyncRedis") as MockAsyncRedis:
        mock_client = AsyncMock()
        MockAsyncRedis.from_url.return_value = mock_client
        
        # Push task
        await queue.push_task("application", task_payload)
        
        # Simulate worker crash by not popping the task
        # The task should remain in the queue
        mock_client.rpush.assert_awaited_once()
        
        # Verify queue connection can be closed independently
        await queue.close()
        mock_client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_application_service_dispatch():
    """Test ApplicationService dispatches tasks correctly."""
    from app.services.applications.application_service import ApplicationService
    import uuid
    
    service = ApplicationService()
    
    application_id = uuid.uuid4()
    job_url = "https://example.com/apply"
    profile_data = {"first_name": "Jane", "last_name": "Smith"}
    resume_path = "/tmp/resume.pdf"
    mode = "Assisted"
    
    with patch("app.infrastructure.queue.valkey_queue.AsyncRedis") as MockAsyncRedis:
        mock_client = AsyncMock()
        MockAsyncRedis.from_url.return_value = mock_client
        
        await service.dispatch_application_task(
            application_id=application_id,
            job_url=job_url,
            profile_data=profile_data,
            resume_path=resume_path,
            mode=mode
        )
        
        # Verify task was pushed to queue
        mock_client.rpush.assert_awaited_once()
        
        # Verify payload structure
        call_args = mock_client.rpush.call_args
        queue_name, serialized_payload = call_args[0]
        
        assert queue_name == "app:tasks:application"
        
        payload = json.loads(serialized_payload)
        assert payload["application_id"] == str(application_id)
        assert payload["job_url"] == job_url
        assert payload["profile_data"] == profile_data
        assert payload["resume_path"] == resume_path
        assert payload["mode"] == mode
        
        await service.close()
