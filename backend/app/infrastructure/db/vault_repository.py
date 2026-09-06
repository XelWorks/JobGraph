import logging
import os
import uuid
from datetime import datetime, timezone

from app.core.config import settings
from app.domain.vault import SessionVault
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _get_aesgcm() -> AESGCM:
    key_hex = settings.master_encryption_key
    if len(key_hex) != 64:
        raise ValueError(
            "master_encryption_key must be a 64-character hex string (32 bytes)"
        )
    key = bytes.fromhex(key_hex)
    return AESGCM(key)


def encrypt_payload(plaintext: str) -> str:
    aesgcm = _get_aesgcm()
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce.hex() + ciphertext.hex()


def decrypt_payload(encrypted: str) -> str:
    aesgcm = _get_aesgcm()
    nonce = bytes.fromhex(encrypted[:24])
    ciphertext = bytes.fromhex(encrypted[24:])
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


class VaultRepository:
    async def save_portal_session(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        portal_name: str,
        session_payload: str,
        status: str = "Healthy",
    ) -> SessionVault:
        encrypted = encrypt_payload(session_payload)
        existing = await self._get_by_user_and_portal(db, user_id, portal_name)
        if existing:
            existing.encrypted_session_payload = encrypted
            existing.status = status
            existing.last_verified_at = datetime.now(timezone.utc)
        else:
            new_entry = SessionVault(
                user_id=user_id,
                portal_name=portal_name,
                status=status,
                encrypted_session_payload=encrypted,
            )
            db.add(new_entry)
            await db.flush()
            await db.commit()
            return new_entry
        await db.commit()
        return existing

    async def get_user_vault(self, db: AsyncSession, user_id: uuid.UUID) -> list[SessionVault]:
        query = select(SessionVault).where(SessionVault.user_id == user_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_portal_session(
        self, db: AsyncSession, user_id: uuid.UUID, portal_name: str
    ) -> SessionVault | None:
        query = select(SessionVault).where(
            SessionVault.user_id == user_id,
            func.lower(SessionVault.portal_name) == portal_name.strip().lower(),
        ).order_by(SessionVault.updated_at.desc()).limit(1)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def delete_portal_session(
        self, db: AsyncSession, user_id: uuid.UUID, portal_name: str
    ) -> bool:
        entry = await self._get_by_user_and_portal(db, user_id, portal_name)
        if not entry:
            return False
        await db.delete(entry)
        await db.commit()
        return True

    async def _get_by_user_and_portal(
        self, db: AsyncSession, user_id: uuid.UUID, portal_name: str
    ) -> SessionVault | None:
        query = select(SessionVault).where(
            SessionVault.user_id == user_id,
            func.lower(SessionVault.portal_name) == portal_name.strip().lower(),
        ).order_by(SessionVault.updated_at.desc()).limit(1)
        result = await db.execute(query)
        return result.scalar_one_or_none()


vault_repository = VaultRepository()
