import logging
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domain.auth import User
from app.infrastructure.db.session import get_db
from app.infrastructure.db.vault_repository import decrypt_payload, vault_repository
from app.services.automation.browser_login_flow import PortalLoginFlow
from app.services.automation.browser_profile_manager import persistent_browser_profile_manager

router = APIRouter()
logger = logging.getLogger(__name__)


class VaultSaveRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    portal_name: str = Field(..., description="Portal name e.g. LinkedIn, Greenhouse")
    session_payload: str = Field(..., description="Encrypted session cookies or tokens as JSON string")
    status: str = Field(default="Healthy", description="Session health status")


class VaultSaveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    portal_name: str
    status: str
    last_verified_at: str


class VaultListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    portal_name: str
    status: str
    last_verified_at: str


class VaultDecryptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    portal_name: str
    session_payload: str


class BrowserLoginRequest(BaseModel):
    portal_name: str = Field(..., description="Portal name to log into, e.g. LinkedIn")


class BrowserLoginResponse(BaseModel):
    portal_name: str
    login_url: str
    profile_dir: str
    message: str


class BrowserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    profile_name: str
    engine: str = "playwright"
    user_agent: str = "local-browser-profile"
    cookie_status: str = "valid"
    storage_status: str = "present"
    last_verified_at: str
    health: str = "Healthy"


@router.post("/browser-login", response_model=BrowserLoginResponse)
async def browser_login_flow(
    payload: BrowserLoginRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        profile = await persistent_browser_profile_manager.launch_profile(payload.portal_name)
    except Exception as exc:
        logger.exception(
            "browser_profile_launch_failed",
            extra={"portal_name": payload.portal_name, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not open the local browser profile. Close any existing automation window and try again.",
        ) from exc
    profile_payload = json.dumps({
        "portal": payload.portal_name.strip().lower(),
        "profile_dir": profile["profile_dir"],
        "auth_mode": "persistent_browser_profile",
    })
    await vault_repository.save_portal_session(
        db=db,
        user_id=current_user.id,
        portal_name=payload.portal_name,
        session_payload=profile_payload,
        status="Healthy",
    )
    return BrowserLoginResponse(
        portal_name=payload.portal_name,
        login_url=profile["login_url"],
        profile_dir=profile["profile_dir"],
        message="Browser opened. Sign in normally; your local profile will be reused automatically.",
    )


@router.get("/profiles", response_model=list[BrowserProfileResponse])
async def list_browser_profiles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entries = await vault_repository.get_user_vault(db, current_user.id)
    profiles: list[BrowserProfileResponse] = []
    for entry in entries:
        session_status = str(entry.status or "Healthy")
        expired = "Reconnect" in session_status or "Expired" in session_status
        cookie_status = "valid" if session_status == "Healthy" else "expired" if expired else "missing"
        storage_status = "present" if entry.encrypted_session_payload else "missing"
        health = "Healthy" if session_status == "Healthy" else session_status
        profiles.append(
            BrowserProfileResponse(
                id=entry.id,
                profile_name=entry.portal_name,
                engine="playwright",
                user_agent="local-browser-profile",
                cookie_status=cookie_status,
                storage_status=storage_status,
                last_verified_at=entry.last_verified_at.isoformat(),
                health=health,
            )
        )
    return profiles


@router.post("/{portal_name}/reconnect", response_model=dict)
async def reconnect_browser_profile(
    portal_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = await vault_repository.get_portal_session(db, current_user.id, portal_name)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portal session '{portal_name}' not found",
        )

    entry.status = "Healthy"
    entry.last_verified_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "portal_name": portal_name,
        "status": "reconnected",
        "login_url": PortalLoginFlow.portal_login_url(portal_name),
        "message": f"Persistent browser profile for {portal_name} is ready to reuse.",
    }


@router.post("/{portal_name}/export-cookies")
async def export_browser_profile_cookies(
    portal_name: str,
    payload: dict | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = await vault_repository.get_portal_session(db, current_user.id, portal_name)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portal session '{portal_name}' not found",
        )

    try:
        decrypted = decrypt_payload(entry.encrypted_session_payload)
    except Exception as exc:
        logger.error("cookie_export_failed for portal %s: %s", portal_name, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt session payload for export",
        ) from exc

    data = {"portal": portal_name, "format": (payload or {}).get("format", "json"), "session_payload": decrypted}
    content = __import__("json").dumps(data, indent=2)
    return Response(content=content, media_type="application/json", headers={"Content-Disposition": f"attachment; filename={portal_name.lower()}-cookies.json"})


@router.post("", response_model=VaultSaveResponse, status_code=status.HTTP_201_CREATED)
async def save_vault_entry(
    payload: VaultSaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        entry = await vault_repository.save_portal_session(
            db=db,
            user_id=current_user.id,
            portal_name=payload.portal_name,
            session_payload=payload.session_payload,
            status=payload.status,
        )
        return VaultSaveResponse(
            id=entry.id,
            user_id=entry.user_id,
            portal_name=entry.portal_name,
            status=entry.status,
            last_verified_at=entry.last_verified_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("", response_model=list[VaultListResponse])
async def list_vault_entries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entries = await vault_repository.get_user_vault(db, current_user.id)
    return [
        VaultListResponse(
            id=e.id,
            portal_name=e.portal_name,
            status=e.status,
            last_verified_at=e.last_verified_at.isoformat(),
        )
        for e in entries
    ]


@router.get("/{portal_name}/decrypt", response_model=VaultDecryptResponse)
async def decrypt_vault_entry(
    portal_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = await vault_repository.get_portal_session(db, current_user.id, portal_name)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portal session '{portal_name}' not found",
        )
    try:
        decrypted = decrypt_payload(entry.encrypted_session_payload)
    except Exception as e:
        logger.error("decryption_failed for portal %s: %s", portal_name, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt session payload",
        ) from e
    return VaultDecryptResponse(portal_name=entry.portal_name, session_payload=decrypted)


@router.delete("/profiles/{profile_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_browser_profile(
    profile_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = await vault_repository.delete_portal_session(db, current_user.id, profile_name)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{profile_name}' not found",
        )


@router.delete("/{portal_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vault_entry(
    portal_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = await vault_repository.delete_portal_session(db, current_user.id, portal_name)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portal session '{portal_name}' not found",
        )
