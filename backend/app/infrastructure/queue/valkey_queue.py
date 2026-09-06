"""Valkey-backed task queue for decoupled browser worker execution."""
import json
import logging
from typing import Any

from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.core.config import settings

logger = logging.getLogger(__name__)


class ValkeyQueue:
    """
    Valkey-backed task queue for asynchronous background job processing.
    
    Provides push_task and pop_task methods for producer-consumer pattern.
    Tasks are serialized as JSON and stored in Redis lists with blocking pop.
    """

    def __init__(self, redis_url: str | None = None) -> None:
        """
        Initialize ValkeyQueue with Redis connection.
        
        Args:
            redis_url: Redis connection URL. Defaults to settings.valkey_url
        """
        self.redis_url = redis_url or settings.valkey_url
        self._client: AsyncRedis | None = None

    async def _get_client(self) -> AsyncRedis:
        """Get or create async Redis client."""
        if self._client is None:
            self._client = AsyncRedis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._client

    async def push_task(self, task_type: str, payload: dict[str, Any]) -> None:
        """
        Push a task to the Valkey queue.
        
        Args:
            task_type: Type of task (e.g., "application", "discovery")
            payload: Task payload as dictionary
        """
        queue_name = f"app:tasks:{task_type}"
        serialized = json.dumps(payload)
        
        client = await self._get_client()
        await client.rpush(queue_name, serialized)
        
        logger.info(
            "task_pushed",
            extra={
                "task_type": task_type,
                "queue_name": queue_name,
                "payload_keys": list(payload.keys())
            }
        )

    async def pop_task(self, task_type: str, timeout: int = 0) -> dict[str, Any] | None:
        """
        Pop a task from the Valkey queue (blocking).
        
        Args:
            task_type: Type of task to pop
            timeout: Blocking timeout in seconds (0 = block indefinitely)
            
        Returns:
            Deserialized task payload or None if queue is empty
        """
        queue_name = f"app:tasks:{task_type}"
        
        client = await self._get_client()
        try:
            result = await client.blpop(queue_name, timeout=timeout)
        except (TimeoutError, RedisTimeoutError):
            # A blocking read may time out while the worker is idle. Keep the
            # connection reusable and let the poll loop try again.
            return None
        
        if result is None:
            return None
        
        # result is tuple: (queue_name, value)
        _, raw_payload = result
        payload = json.loads(raw_payload)
        
        logger.info(
            "task_popped",
            extra={
                "task_type": task_type,
                "queue_name": queue_name,
                "payload_keys": list(payload.keys())
            }
        )
        
        return payload

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None
