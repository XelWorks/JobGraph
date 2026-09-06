import logging
from typing import Any

from app.domain.connector import BasePortalConnector
from app.services.discovery.connector import (
    GlassdoorConnector,
    GreenhouseConnector,
    LeverConnector,
    LinkedInConnector,
    NaukriConnector,
)

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    def __init__(self, *, register_defaults: bool = True) -> None:
        self._connectors: dict[str, type[BasePortalConnector]] = {}
        if register_defaults:
            self.register("Greenhouse", GreenhouseConnector)
            self.register("Lever", LeverConnector)
            self.register("LinkedIn", LinkedInConnector)
            self.register("Naukri", NaukriConnector)
            self.register("Glassdoor", GlassdoorConnector)

    def register(self, platform_name: str, connector_cls: type[BasePortalConnector]) -> None:
        self._connectors[platform_name.lower()] = connector_cls
        logger.info("connector_registered: platform=%s", platform_name)

    def get_connector(self, platform_name: str) -> type[BasePortalConnector] | None:
        return self._connectors.get(platform_name.lower())

    def list_platforms(self) -> list[str]:
        return list(self._connectors.keys())

    def create_connector(self, platform_name: str, **kwargs: Any) -> BasePortalConnector | None:
        connector_cls = self._connectors.get(platform_name.lower())
        if connector_cls is None:
            logger.warning("connector_not_found: platform=%s", platform_name)
            return None
        return connector_cls(**kwargs)


connector_registry = ConnectorRegistry(register_defaults=True)
