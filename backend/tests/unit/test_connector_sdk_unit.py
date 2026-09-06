import pytest
from app.domain.connector import BasePortalConnector
from app.services.discovery.connector import (
    GlassdoorConnector,
    GreenhouseConnector,
    LeverConnector,
    LinkedInConnector,
    NaukriConnector,
)
from app.services.discovery.connector_sdk import ConnectorRegistry, connector_registry


class TestBasePortalConnector:
    def test_base_connector_is_abstract(self):
        with pytest.raises(TypeError):
            BasePortalConnector()

    def test_greenhouse_connector_implements_all_methods(self):
        connector = GreenhouseConnector()
        assert hasattr(connector, "connect")
        assert hasattr(connector, "disconnect")
        assert hasattr(connector, "validate_session")
        assert hasattr(connector, "search_jobs")
        assert hasattr(connector, "apply")
        assert hasattr(connector, "health_check")
        assert hasattr(connector, "refresh_session")

    def test_lever_connector_implements_all_methods(self):
        connector = LeverConnector()
        assert hasattr(connector, "connect")
        assert hasattr(connector, "disconnect")
        assert hasattr(connector, "validate_session")
        assert hasattr(connector, "search_jobs")
        assert hasattr(connector, "apply")
        assert hasattr(connector, "health_check")
        assert hasattr(connector, "refresh_session")

    def test_linkedin_connector_implements_all_methods(self):
        connector = LinkedInConnector()
        assert hasattr(connector, "connect")
        assert hasattr(connector, "disconnect")
        assert hasattr(connector, "validate_session")
        assert hasattr(connector, "search_jobs")
        assert hasattr(connector, "apply")
        assert hasattr(connector, "health_check")
        assert hasattr(connector, "refresh_session")

    def test_naukri_connector_implements_all_methods(self):
        connector = NaukriConnector()
        assert hasattr(connector, "connect")
        assert hasattr(connector, "disconnect")
        assert hasattr(connector, "validate_session")
        assert hasattr(connector, "search_jobs")
        assert hasattr(connector, "apply")
        assert hasattr(connector, "health_check")
        assert hasattr(connector, "refresh_session")

    def test_glassdoor_connector_implements_all_methods(self):
        connector = GlassdoorConnector()
        assert hasattr(connector, "connect")
        assert hasattr(connector, "disconnect")
        assert hasattr(connector, "validate_session")
        assert hasattr(connector, "search_jobs")
        assert hasattr(connector, "apply")
        assert hasattr(connector, "health_check")
        assert hasattr(connector, "refresh_session")


class TestConnectorRegistry:
    def test_registry_starts_with_default_supported_platforms(self):
        registry = ConnectorRegistry()
        platforms = registry.list_platforms()
        assert "greenhouse" in platforms
        assert "lever" in platforms
        assert "linkedin" in platforms
        assert "naukri" in platforms
        assert "glassdoor" in platforms

    def test_register_and_get_connector(self):
        registry = ConnectorRegistry()
        registry.register("Greenhouse", GreenhouseConnector)
        assert registry.get_connector("Greenhouse") is GreenhouseConnector
        assert registry.get_connector("greenhouse") is GreenhouseConnector

    def test_get_connector_not_registered(self):
        registry = ConnectorRegistry()
        assert registry.get_connector("NonExistent") is None

    def test_list_platforms(self):
        registry = ConnectorRegistry()
        registry.register("Greenhouse", GreenhouseConnector)
        registry.register("Lever", LeverConnector)
        registry.register("LinkedIn", LinkedInConnector)
        registry.register("Naukri", NaukriConnector)
        registry.register("Glassdoor", GlassdoorConnector)
        platforms = registry.list_platforms()
        assert "greenhouse" in platforms
        assert "lever" in platforms
        assert "linkedin" in platforms
        assert "naukri" in platforms
        assert "glassdoor" in platforms
        assert len(platforms) == 5

    def test_create_connector(self):
        registry = ConnectorRegistry()
        registry.register("Greenhouse", GreenhouseConnector)
        connector = registry.create_connector("Greenhouse")
        assert isinstance(connector, GreenhouseConnector)

    def test_create_connector_not_registered(self):
        registry = ConnectorRegistry()
        connector = registry.create_connector("NonExistent")
        assert connector is None

    def test_singleton_registry(self):
        connector_registry.register("Greenhouse", GreenhouseConnector)
        assert connector_registry.get_connector("Greenhouse") is GreenhouseConnector
        assert "greenhouse" in connector_registry.list_platforms()


class TestGreenhouseConnectorMethods:
    @pytest.mark.asyncio
    async def test_connect_returns_true(self):
        connector = GreenhouseConnector()
        result = await connector.connect({"board_token": "mock"})
        assert result is True

    @pytest.mark.asyncio
    async def test_disconnect(self):
        connector = GreenhouseConnector()
        await connector.disconnect()

    @pytest.mark.asyncio
    async def test_validate_session(self):
        connector = GreenhouseConnector()
        result = await connector.validate_session()
        assert result is True

    @pytest.mark.asyncio
    async def test_search_jobs_returns_empty(self):
        connector = GreenhouseConnector()
        result = await connector.search_jobs("python", "Remote")
        assert result == []

    @pytest.mark.asyncio
    async def test_apply_returns_not_implemented(self):
        connector = GreenhouseConnector()
        result = await connector.apply("https://example.com", {}, "/tmp/resume.pdf")
        assert result == {"status": "not_implemented"}

    @pytest.mark.asyncio
    async def test_health_check(self):
        connector = GreenhouseConnector()
        result = await connector.health_check()
        assert result == "Healthy"

    @pytest.mark.asyncio
    async def test_refresh_session(self):
        connector = GreenhouseConnector()
        result = await connector.refresh_session()
        assert result == {}


class TestLeverConnectorMethods:
    @pytest.mark.asyncio
    async def test_connect_returns_true(self):
        connector = LeverConnector()
        result = await connector.connect({"board_token": "mock"})
        assert result is True

    @pytest.mark.asyncio
    async def test_disconnect(self):
        connector = LeverConnector()
        await connector.disconnect()

    @pytest.mark.asyncio
    async def test_validate_session(self):
        connector = LeverConnector()
        result = await connector.validate_session()
        assert result is True

    @pytest.mark.asyncio
    async def test_search_jobs_returns_empty(self):
        connector = LeverConnector()
        result = await connector.search_jobs("python", "Remote")
        assert result == []

    @pytest.mark.asyncio
    async def test_apply_returns_not_implemented(self):
        connector = LeverConnector()
        result = await connector.apply("https://example.com", {}, "/tmp/resume.pdf")
        assert result == {"status": "not_implemented"}

    @pytest.mark.asyncio
    async def test_health_check(self):
        connector = LeverConnector()
        result = await connector.health_check()
        assert result == "Healthy"

    @pytest.mark.asyncio
    async def test_refresh_session(self):
        connector = LeverConnector()
        result = await connector.refresh_session()
        assert result == {}


class TestConnectorRegistryIntegration:
    def test_greenhouse_connector_inherits_base(self):
        connector = GreenhouseConnector()
        assert isinstance(connector, BasePortalConnector)

    def test_lever_connector_inherits_base(self):
        connector = LeverConnector()
        assert isinstance(connector, BasePortalConnector)

    def test_linkedin_connector_inherits_base(self):
        connector = LinkedInConnector()
        assert isinstance(connector, BasePortalConnector)

    def test_naukri_connector_inherits_base(self):
        connector = NaukriConnector()
        assert isinstance(connector, BasePortalConnector)

    def test_glassdoor_connector_inherits_base(self):
        connector = GlassdoorConnector()
        assert isinstance(connector, BasePortalConnector)

    @pytest.mark.asyncio
    async def test_browser_ready_portal_connectors_include_chrome_session_context(self):
        connectors = [
            LinkedInConnector(),
            NaukriConnector(),
            GlassdoorConnector(),
        ]

        for connector in connectors:
            result = await connector.apply(
                "https://example.com/job/123",
                {"first_name": "Jane", "last_name": "Doe"},
                "/tmp/resume.pdf",
            )

            assert result["status"] == "browser_ready"
            assert result["browser"] == "chrome"
            assert result["requires_review"] is True
            assert result["portal"] in {"linkedin", "naukri", "glassdoor"}
            assert result["browser_context"]["browser"] == "chrome"
            assert result["browser_context"]["portal"] == result["portal"]
            assert result["browser_context"]["manual_review_required"] is True

    def test_registry_can_instantiate_connectors(self):
        registry = ConnectorRegistry()
        registry.register("Greenhouse", GreenhouseConnector)
        registry.register("Lever", LeverConnector)
        registry.register("LinkedIn", LinkedInConnector)
        registry.register("Naukri", NaukriConnector)
        registry.register("Glassdoor", GlassdoorConnector)

        gh = registry.create_connector("Greenhouse")
        lv = registry.create_connector("Lever")
        li = registry.create_connector("LinkedIn")
        nk = registry.create_connector("Naukri")
        gd = registry.create_connector("Glassdoor")

        assert isinstance(gh, GreenhouseConnector)
        assert isinstance(lv, LeverConnector)
        assert isinstance(li, LinkedInConnector)
        assert isinstance(nk, NaukriConnector)
        assert isinstance(gd, GlassdoorConnector)
        assert isinstance(gh, BasePortalConnector)
        assert isinstance(lv, BasePortalConnector)
        assert isinstance(li, BasePortalConnector)
        assert isinstance(nk, BasePortalConnector)
        assert isinstance(gd, BasePortalConnector)
