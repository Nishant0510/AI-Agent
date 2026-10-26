"""Password hashing, signed access tokens, and authentication dependencies."""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.services.database import get_user_by_id
from app.utils.config import settings

password_hash = PasswordHash.recommended()
_DUMMY_PASSWORD_HASH = password_hash.hash("not-a-real-account-password")
_bearer = HTTPBearer(auto_error=False)
_JWT_ALGORITHM = "HS256"
AUTH_COOKIE_NAME = "philips_access_token"


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    return password_hash.verify(password, stored_hash)


def verify_unknown_account_password(password: str) -> None:
    """Reduce account-enumeration timing differences during failed logins."""
    password_hash.verify(password, _DUMMY_PASSWORD_HASH)


def create_access_token(user_id: UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=_JWT_ALGORITHM)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any]:
    token = credentials.credentials if credentials else request.cookies.get(AUTH_COOKIE_NAME)
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token or not settings.jwt_secret_key:
        raise unauthorized
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[_JWT_ALGORITHM])
        user_id = UUID(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise unauthorized from exc
    user = get_user_by_id(user_id)
    if user is None:
        raise unauthorized
    return user


def require_admin(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return user
