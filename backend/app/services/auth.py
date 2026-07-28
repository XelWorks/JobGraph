import logging
from datetime import datetime, timedelta, timezone

import jwt
from app.core.config import settings
from app.domain.auth import User
from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("app.services.auth")

password_hasher = PasswordHasher()

def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return password_hasher.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against an Argon2id hash."""
    try:
        return password_hasher.verify(hashed_password, password)
    except Exception:
        return False

def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Generate a JWT access token for a given user subject."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    to_encode = {"sub": subject, "exp": expire}
    secret_key = settings.jwt_secret_key
    if secret_key == "CHANGE_THIS_TO_RANDOM_HEX_32_BYTES_FOR_JWT":
        secret_key = settings.master_encryption_key

    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT access token."""
    try:
        secret_key = settings.jwt_secret_key
        if secret_key == "CHANGE_THIS_TO_RANDOM_HEX_32_BYTES_FOR_JWT":
            secret_key = settings.master_encryption_key

        payload = jwt.decode(token, secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.PyJWTError as e:
        logger.warning(f"token_decoding_failed: {e}")
        return None

async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    first_name: str | None = None,
    last_name: str | None = None
) -> User:
    """Register a new user after verifying that the email is unique."""
    existing_user_query = await db.execute(select(User).where(User.email == email))
    if existing_user_query.scalar_one_or_none():
        raise ValueError("User with this email already exists.")

    hashed = hash_password(password)
    new_user = User(
        email=email,
        hashed_password=hashed,
        first_name=first_name,
        last_name=last_name,
        is_active=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Authenticate a user by validating their credentials."""
    user_query = await db.execute(select(User).where(User.email == email))
    user = user_query.scalar_one_or_none()
    if not user:
        # Perform dummy verify to mitigate timing attacks / account enumeration
        verify_password(password, "$argon2id$v=19$m=65536,t=3,p=4$dummyhashdummyhashdummy")
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user
