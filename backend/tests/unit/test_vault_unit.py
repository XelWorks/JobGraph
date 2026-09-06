import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.domain.vault import SessionVault
from app.infrastructure.db.vault_repository import (
    decrypt_payload,
    encrypt_payload,
    vault_repository,
)
from cryptography.exceptions import InvalidTag

VALID_HEX_KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


class TestEncryptionRoundTrip:
    def test_encrypt_decrypt_round_trip(self):
        with patch("app.infrastructure.db.vault_repository.settings") as mock_settings:
            mock_settings.master_encryption_key = VALID_HEX_KEY
            plaintext = '{"cookies": "session=abc123; csrf=xyz789"}'
            encrypted = encrypt_payload(plaintext)
            assert encrypted != plaintext
            assert len(encrypted) > len(plaintext)
            decrypted = decrypt_payload(encrypted)
            assert decrypted == plaintext

    def test_encrypt_produces_different_ciphertext_each_time(self):
        with patch("app.infrastructure.db.vault_repository.settings") as mock_settings:
            mock_settings.master_encryption_key = VALID_HEX_KEY
            plaintext = '{"token": "secret-value"}'
            encrypted1 = encrypt_payload(plaintext)
            encrypted2 = encrypt_payload(plaintext)
            assert encrypted1 != encrypted2

    def test_decrypt_invalid_payload_raises_error(self):
        with pytest.raises(ValueError):
            decrypt_payload("not_valid_hex")

    def test_decrypt_tampered_ciphertext_raises_error(self):
        with patch("app.infrastructure.db.vault_repository.settings") as mock_settings:
            mock_settings.master_encryption_key = VALID_HEX_KEY
            plaintext = '{"cookies": "session=abc123"}'
            encrypted = encrypt_payload(plaintext)
            tampered = encrypted[:-4] + "ffff"
            with pytest.raises(InvalidTag):
                decrypt_payload(tampered)


class TestVaultRepositorySave:
    @pytest.mark.asyncio
    async def test_save_portal_session_creates_new_entry(self):
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.flush = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        user_id = uuid.uuid4()
        portal_name = "LinkedIn"
        session_payload = '{"cookies": "session=abc"}'

        with patch.object(vault_repository, "_get_by_user_and_portal", AsyncMock(return_value=None)):
            with patch("app.infrastructure.db.vault_repository.settings") as mock_settings:
                mock_settings.master_encryption_key = VALID_HEX_KEY
                result = await vault_repository.save_portal_session(
                    db=mock_db,
                    user_id=user_id,
                    portal_name=portal_name,
                    session_payload=session_payload,
                )

        assert result is not None
        assert result.portal_name == portal_name
        assert result.user_id == user_id
        assert result.status == "Healthy"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_save_portal_session_updates_existing_entry(self):
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        existing_entry = SessionVault(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            portal_name="LinkedIn",
            status="Healthy",
            encrypted_session_payload="old_encrypted",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_entry
        mock_db.execute.return_value = mock_result

        user_id = existing_entry.user_id
        portal_name = "LinkedIn"
        session_payload = '{"cookies": "session=new"}'

        with patch.object(vault_repository, "_get_by_user_and_portal", AsyncMock(return_value=existing_entry)):
            with patch("app.infrastructure.db.vault_repository.settings") as mock_settings:
                mock_settings.master_encryption_key = VALID_HEX_KEY
                result = await vault_repository.save_portal_session(
                    db=mock_db,
                    user_id=user_id,
                    portal_name=portal_name,
                    session_payload=session_payload,
                )

        assert result is not None
        assert result.portal_name == portal_name
        mock_db.commit.assert_called()


class TestVaultRepositoryGet:
    @pytest.mark.asyncio
    async def test_get_user_vault_returns_entries(self):
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()

        user_id = uuid.uuid4()
        entry = SessionVault(
            id=uuid.uuid4(),
            user_id=user_id,
            portal_name="LinkedIn",
            status="Healthy",
            encrypted_session_payload="encrypted_data",
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [entry]
        mock_db.execute.return_value = mock_result

        result = await vault_repository.get_user_vault(db=mock_db, user_id=user_id)

        assert len(result) == 1
        assert result[0].portal_name == "LinkedIn"
        assert result[0].status == "Healthy"

    @pytest.mark.asyncio
    async def test_get_user_vault_returns_empty_list(self):
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()

        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await vault_repository.get_user_vault(db=mock_db, user_id=user_id)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_portal_session_returns_entry(self):
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()

        user_id = uuid.uuid4()
        portal_name = "LinkedIn"
        entry = SessionVault(
            id=uuid.uuid4(),
            user_id=user_id,
            portal_name=portal_name,
            status="Healthy",
            encrypted_session_payload="encrypted_data",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = entry
        mock_db.execute.return_value = mock_result

        result = await vault_repository.get_portal_session(
            db=mock_db, user_id=user_id, portal_name=portal_name
        )

        assert result is not None
        assert result.portal_name == portal_name

    @pytest.mark.asyncio
    async def test_get_portal_session_returns_none_when_missing(self):
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()

        user_id = uuid.uuid4()
        portal_name = "LinkedIn"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await vault_repository.get_portal_session(
            db=mock_db, user_id=user_id, portal_name=portal_name
        )

        assert result is None


class TestVaultRepositoryDelete:
    @pytest.mark.asyncio
    async def test_delete_portal_session_returns_true(self):
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        user_id = uuid.uuid4()
        portal_name = "LinkedIn"
        entry = SessionVault(
            id=uuid.uuid4(),
            user_id=user_id,
            portal_name=portal_name,
            status="Healthy",
            encrypted_session_payload="encrypted_data",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = entry
        mock_db.execute.return_value = mock_result

        with patch.object(vault_repository, "_get_by_user_and_portal", AsyncMock(return_value=entry)):
            result = await vault_repository.delete_portal_session(
                db=mock_db, user_id=user_id, portal_name=portal_name
            )

        assert result is True
        mock_db.delete.assert_called_once_with(entry)
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_delete_portal_session_returns_false_when_not_found(self):
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()

        user_id = uuid.uuid4()
        portal_name = "LinkedIn"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch.object(vault_repository, "_get_by_user_and_portal", AsyncMock(return_value=None)):
            result = await vault_repository.delete_portal_session(
                db=mock_db, user_id=user_id, portal_name=portal_name
            )

        assert result is False


class TestVaultRepositoryEncryptionKey:
    def test_encrypt_payload_with_invalid_key_length_raises_error(self):
        with patch("app.infrastructure.db.vault_repository.settings") as mock_settings:
            mock_settings.master_encryption_key = "short_key"
            with pytest.raises(ValueError, match="64-character hex string"):
                encrypt_payload("test")
