import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.domain.connector import BasePortalConnector
from app.domain.vault import SessionVault
from app.infrastructure.db.vault_repository import (
    VaultRepository,
    decrypt_payload,
    encrypt_payload,
)
from app.services.discovery.connector import GreenhouseConnector, LeverConnector
from app.services.discovery.connector_sdk import ConnectorRegistry

VALID_HEX_KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


@pytest.fixture
def registered_registry():
    registry = ConnectorRegistry(register_defaults=False)
    registry.register("Greenhouse", GreenhouseConnector)
    registry.register("Lever", LeverConnector)
    return registry


@pytest.fixture
def mock_vault_session():
    return {
        "portal_name": "Greenhouse",
        "session_data": {"board_token": "test_token", "cookies": "session=abc123"},
        "status": "Healthy",
    }


class TestBasePortalConnector:
    REQUIRED_METHODS = [
        "connect",
        "disconnect",
        "validate_session",
        "search_jobs",
        "apply",
        "health_check",
        "refresh_session",
    ]

    def test_base_portal_connector_is_abstract(self):
        with pytest.raises(TypeError):
            BasePortalConnector()

    def test_greenhouse_is_base_portal_connector(self, registered_registry):
        connector = registered_registry.create_connector("Greenhouse")
        assert isinstance(connector, BasePortalConnector)
        assert isinstance(connector, GreenhouseConnector)

    def test_lever_is_base_portal_connector(self, registered_registry):
        connector = registered_registry.create_connector("Lever")
        assert isinstance(connector, BasePortalConnector)
        assert isinstance(connector, LeverConnector)

    def test_greenhouse_implements_all_required_methods(self, registered_registry):
        connector = registered_registry.create_connector("Greenhouse")
        for method_name in self.REQUIRED_METHODS:
            assert callable(getattr(connector, method_name)), (
                f"GreenhouseConnector is missing required method: {method_name}"
            )

    def test_lever_implements_all_required_methods(self, registered_registry):
        connector = registered_registry.create_connector("Lever")
        for method_name in self.REQUIRED_METHODS:
            assert callable(getattr(connector, method_name)), (
                f"LeverConnector is missing required method: {method_name}"
            )

    @pytest.mark.asyncio
    async def test_greenhouse_disconnect_returns_none(self, registered_registry):
        connector = registered_registry.create_connector("Greenhouse")
        result = await connector.disconnect()
        assert result is None

    @pytest.mark.asyncio
    async def test_lever_disconnect_returns_none(self, registered_registry):
        connector = registered_registry.create_connector("Lever")
        result = await connector.disconnect()
        assert result is None


class TestConnectorRegistryInstantiation:
    def test_get_connector_returns_connector_class(self, registered_registry):
        connector_cls = registered_registry.get_connector("Greenhouse")
        assert connector_cls is GreenhouseConnector

    def test_get_connector_case_insensitive(self, registered_registry):
        connector_cls = registered_registry.get_connector("greenhouse")
        assert connector_cls is GreenhouseConnector

    def test_get_connector_not_registered(self, registered_registry):
        assert registered_registry.get_connector("NonExistent") is None

    def test_create_connector_instantiates(self, registered_registry):
        connector = registered_registry.create_connector("Greenhouse")
        assert isinstance(connector, GreenhouseConnector)
        assert isinstance(connector, BasePortalConnector)

    def test_create_connector_not_registered(self, registered_registry):
        assert registered_registry.create_connector("NonExistent") is None

    def test_list_platforms(self, registered_registry):
        platforms = registered_registry.list_platforms()
        assert "greenhouse" in platforms
        assert "lever" in platforms
        assert len(platforms) == 2


class TestConnectorHealthCheckAndSessionValidation:
    @pytest.mark.asyncio
    async def test_greenhouse_health_check(self, registered_registry):
        connector = registered_registry.create_connector("Greenhouse")
        result = await connector.health_check()
        assert result == "Healthy"

    @pytest.mark.asyncio
    async def test_lever_health_check(self, registered_registry):
        connector = registered_registry.create_connector("Lever")
        result = await connector.health_check()
        assert result == "Healthy"

    @pytest.mark.asyncio
    async def test_greenhouse_validate_session(self, registered_registry):
        connector = registered_registry.create_connector("Greenhouse")
        result = await connector.validate_session()
        assert result is True

    @pytest.mark.asyncio
    async def test_lever_validate_session(self, registered_registry):
        connector = registered_registry.create_connector("Lever")
        result = await connector.validate_session()
        assert result is True

    @pytest.mark.asyncio
    async def test_all_registered_connectors_health_check(self, registered_registry):
        for platform in registered_registry.list_platforms():
            connector = registered_registry.create_connector(platform)
            assert connector is not None
            result = await connector.health_check()
            assert result == "Healthy"

    @pytest.mark.asyncio
    async def test_all_registered_connectors_validate_session(self, registered_registry):
        for platform in registered_registry.list_platforms():
            connector = registered_registry.create_connector(platform)
            assert connector is not None
            result = await connector.validate_session()
            assert result is True


class TestConnectorSessionPayloadApplication:
    @pytest.mark.asyncio
    async def test_greenhouse_connect_applies_session_payload(self, registered_registry, mock_vault_session):
        connector = registered_registry.create_connector("Greenhouse")
        result = await connector.connect(mock_vault_session["session_data"])
        assert result is True

    @pytest.mark.asyncio
    async def test_lever_connect_applies_session_payload(self, registered_registry, mock_vault_session):
        connector = registered_registry.create_connector("Lever")
        result = await connector.connect(mock_vault_session["session_data"])
        assert result is True

    @pytest.mark.asyncio
    async def test_connector_refresh_session_returns_dict(self, registered_registry):
        for platform in registered_registry.list_platforms():
            connector = registered_registry.create_connector(platform)
            result = await connector.refresh_session()
            assert isinstance(result, dict)


class TestConnectorDiscoveryAndFormSubmissionMocked:
    @pytest.mark.asyncio
    async def test_greenhouse_search_jobs_returns_list(self, registered_registry):
        connector = registered_registry.create_connector("Greenhouse")
        result = await connector.search_jobs("python", "Remote")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_lever_search_jobs_returns_list(self, registered_registry):
        connector = registered_registry.create_connector("Lever")
        result = await connector.search_jobs("python", "Remote")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_greenhouse_apply_returns_dict(self, registered_registry):
        connector = registered_registry.create_connector("Greenhouse")
        result = await connector.apply(
            "https://example.com/job/1",
            {"name": "Test Candidate"},
            "/tmp/resume.pdf",
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_lever_apply_returns_dict(self, registered_registry):
        connector = registered_registry.create_connector("Lever")
        result = await connector.apply(
            "https://example.com/job/1",
            {"name": "Test Candidate"},
            "/tmp/resume.pdf",
        )
        assert isinstance(result, dict)


class TestConnectorSDKWithMockedVault:
    @pytest.mark.asyncio
    async def test_session_vault_payload_applied_to_connector(self, registered_registry, mock_vault_session):
        with patch(
            "app.services.discovery.connector.GreenhouseConnector.connect"
        ) as mock_connect:
            mock_connect.return_value = True
            connector = registered_registry.create_connector("Greenhouse")
            result = await connector.connect(mock_vault_session["session_data"])
            mock_connect.assert_called_once_with(mock_vault_session["session_data"])
            assert result is True

    @pytest.mark.asyncio
    async def test_connector_health_check_after_vault_session(self, registered_registry, mock_vault_session):
        connector = registered_registry.create_connector("Greenhouse")
        await connector.connect(mock_vault_session["session_data"])
        health = await connector.health_check()
        assert health == "Healthy"

    @pytest.mark.asyncio
    async def test_connector_validate_session_after_vault_session(self, registered_registry, mock_vault_session):
        connector = registered_registry.create_connector("Greenhouse")
        await connector.connect(mock_vault_session["session_data"])
        valid = await connector.validate_session()
        assert valid is True


class TestConnectorSessionVaultIntegration:
    """Verifies that encrypted session profiles are loaded from the Session
    Vault (Epic 7), decrypted, and applied cleanly to a connector's connect()
    call through the unified Connector SDK (Epic 8)."""

    def _build_vault_entry(self, portal_name, session_payload):
        with patch("app.infrastructure.db.vault_repository.settings") as mock_settings:
            mock_settings.master_encryption_key = VALID_HEX_KEY
            encrypted = encrypt_payload(session_payload)
            decrypted = decrypt_payload(encrypted)
        entry = SessionVault(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            portal_name=portal_name,
            status="Healthy",
            encrypted_session_payload=encrypted,
        )
        return entry, decrypted

    def _mock_db_returning(self, entry):
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = entry
        mock_db.execute.return_value = mock_result
        return mock_db

    @pytest.mark.asyncio
    async def test_greenhouse_vault_session_payload_applied_to_connector(self, registered_registry):
        session_payload = '{"board_token": "gh_test_token", "cookies": "session=abc123"}'
        entry, decrypted = self._build_vault_entry("Greenhouse", session_payload)
        assert decrypted == session_payload

        mock_db = self._mock_db_returning(entry)
        repo = VaultRepository()
        retrieved = await repo.get_portal_session(
            db=mock_db, user_id=entry.user_id, portal_name="Greenhouse"
        )
        assert retrieved is not None
        assert retrieved.portal_name == "Greenhouse"
        assert retrieved.encrypted_session_payload == entry.encrypted_session_payload

        session_data = json.loads(decrypted)
        connector = registered_registry.create_connector("Greenhouse")
        result = await connector.connect(session_data)
        assert result is True
        assert session_data["board_token"] == "gh_test_token"
        assert session_data["cookies"] == "session=abc123"

    @pytest.mark.asyncio
    async def test_lever_vault_session_payload_applied_to_connector(self, registered_registry):
        session_payload = '{"board_token": "lever_test_token", "cookies": "session=xyz789"}'
        entry, decrypted = self._build_vault_entry("Lever", session_payload)
        assert decrypted == session_payload

        mock_db = self._mock_db_returning(entry)
        repo = VaultRepository()
        retrieved = await repo.get_portal_session(
            db=mock_db, user_id=entry.user_id, portal_name="Lever"
        )
        assert retrieved is not None
        assert retrieved.portal_name == "Lever"

        session_data = json.loads(decrypted)
        connector = registered_registry.create_connector("Lever")
        result = await connector.connect(session_data)
        assert result is True
        assert session_data["board_token"] == "lever_test_token"

    @pytest.mark.asyncio
    async def test_vault_session_payload_round_trip_through_connector(self, registered_registry):
        session_payload = '{"board_token": "gh_round_trip", "cookies": "session=roundtrip"}'
        entry, decrypted = self._build_vault_entry("Greenhouse", session_payload)

        mock_db = self._mock_db_returning(entry)
        repo = VaultRepository()
        retrieved = await repo.get_portal_session(
            db=mock_db, user_id=entry.user_id, portal_name="Greenhouse"
        )
        assert retrieved is not None

        with patch("app.infrastructure.db.vault_repository.settings") as mock_settings:
            mock_settings.master_encryption_key = VALID_HEX_KEY
            re_decrypted = decrypt_payload(retrieved.encrypted_session_payload)
        assert re_decrypted == decrypted == session_payload

        session_data = json.loads(re_decrypted)
        connector = registered_registry.create_connector("Greenhouse")
        result = await connector.connect(session_data)
        assert result is True
