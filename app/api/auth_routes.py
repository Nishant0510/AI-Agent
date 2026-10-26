"""Signup, login, logout, and current-user endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.models.schemas import AuthRequest, AuthResponse, UserResponse
from app.services.database import (
    DuplicateEmailError,
    create_user,
    get_user_by_email,
)
from app.services.security import (
    AUTH_COOKIE_NAME,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
    verify_unknown_account_password,
)
from app.utils.config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])


def _response_for_user(user: dict) -> AuthResponse:
    token = create_access_token(user["id"])
    return AuthResponse(
        access_token=token,
        user=UserResponse(id=user["id"], email=user["email"], role=user["role"]),
    )


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: AuthRequest, response: Response):
    if payload.email == settings.admin_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is reserved for the administrator account.",
        )
    try:
        user = create_user(payload.email, hash_password(payload.password))
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    result = _response_for_user(user)
    _set_auth_cookie(response, result.access_token)
    return result


@router.post("/login", response_model=AuthResponse)
def login(payload: AuthRequest, response: Response):
    user = get_user_by_email(payload.email)
    if user is None:
        verify_unknown_account_password(payload.password)
    valid_password = bool(user) and verify_password(payload.password, user["password_hash"])
    if not valid_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    result = _response_for_user(user)
    _set_auth_cookie(response, result.access_token)
    return result


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )
    response.status_code = status.HTTP_204_NO_CONTENT


@router.get("/me", response_model=UserResponse)
def current_user(user: dict = Depends(get_current_user)):
    return UserResponse(id=user["id"], email=user["email"], role=user["role"])
