import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.queue.valkey_queue import ValkeyQueue


@pytest.mark.asyncio
async def test_push_task_serializes_payload_and_pushes_to_list():
    queue = ValkeyQueue()
    task_type = "application"
    payload = {"application_id": "123", "url": "https://example.com/apply"}

    with patch("app.infrastructure.queue.valkey_queue.AsyncRedis") as MockAsyncRedis:
        mock_client = AsyncMock()
        MockAsyncRedis.from_url.return_value = mock_client

        await queue.push_task(task_type, payload)

        expected_queue_name = "app:tasks:application"
        mock_client.rpush.assert_awaited_once_with(
            expected_queue_name, json.dumps(payload)
        )


@pytest.mark.asyncio
async def test_pop_task_blocks_and_returns_deserialized_payload():
    queue = ValkeyQueue()
    raw_payload = json.dumps({"application_id": "456", "url": "https://example.com/apply"})

    with patch("app.infrastructure.queue.valkey_queue.AsyncRedis") as MockAsyncRedis:
        mock_client = AsyncMock()
        mock_client.blpop.return_value = ("app:tasks:application", raw_payload)
        MockAsyncRedis.from_url.return_value = mock_client

        result = await queue.pop_task("application")

        mock_client.blpop.assert_awaited_once_with("app:tasks:application", timeout=0)
        assert result == {"application_id": "456", "url": "https://example.com/apply"}


@pytest.mark.asyncio
async def test_pop_task_returns_none_when_queue_empty():
    queue = ValkeyQueue()

    with patch("app.infrastructure.queue.valkey_queue.AsyncRedis") as MockAsyncRedis:
        mock_client = AsyncMock()
        mock_client.blpop.return_value = None
        MockAsyncRedis.from_url.return_value = mock_client

        result = await queue.pop_task("application")

        assert result is None


@pytest.mark.asyncio
async def test_queue_close_closes_client():
    queue = ValkeyQueue()

    with patch("app.infrastructure.queue.valkey_queue.AsyncRedis") as MockAsyncRedis:
        mock_client = AsyncMock()
        MockAsyncRedis.from_url.return_value = mock_client

        # Initialize client by calling a method
        await queue.push_task("test", {"data": "test"})

        # Close the queue
        await queue.close()

        # Verify close was called
        mock_client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_queue_uses_custom_redis_url():
    custom_url = "redis://custom:6379/1"
    queue = ValkeyQueue(redis_url=custom_url)

    with patch("app.infrastructure.queue.valkey_queue.AsyncRedis") as MockAsyncRedis:
        mock_client = AsyncMock()
        MockAsyncRedis.from_url.return_value = mock_client

        await queue.push_task("test", {"data": "test"})

        # Verify from_url was called with custom URL
        MockAsyncRedis.from_url.assert_called_once()
        call_args = MockAsyncRedis.from_url.call_args
        assert call_args[0][0] == custom_url
