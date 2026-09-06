from abc import ABC, abstractmethod
from typing import Any


class BasePortalConnector(ABC):
    @abstractmethod
    async def connect(self, session_data: dict[str, Any]) -> bool:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def validate_session(self) -> bool:
        pass

    @abstractmethod
    async def search_jobs(self, query: str, location: str) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def apply(self, job_url: str, profile_data: dict[str, Any], resume_path: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def health_check(self) -> str:
        pass

    @abstractmethod
    async def refresh_session(self) -> dict[str, Any]:
        pass
