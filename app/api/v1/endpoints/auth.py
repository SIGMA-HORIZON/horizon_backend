"""
Auth Endpoints — /api/v1/auth

Public and authenticated endpoints for the user authentication lifecycle:
registration requests, login, logout, and password management.

Routes:
  - POST /register-request  → Public. Submit an account signup request.
  - POST /login             → Public. Authenticate and receive a JWT token.
  - POST /logout            → Authenticated. Invalidate the current session.
  - POST /change-password   → Authenticated. Change the logged-in user's password.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, Request, status, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.api.deps import get_current_user
from app.schemas.auth import (
    RegisterRequest,
    RegisterRequestResponse,
    LoginRequest,
    TokenResponse,
    LogoutResponse,
    ChangePasswordRequest,
)
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository
from app.services.email_service import EmailService
from app.services.auth_service import AuthService
from app.core.security import create_access_token
from app.core.config import settings
from app.models.base_models import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Construct AuthService with all required repositories injected."""
    user_repo = UserRepository(db)
    audit_repo = AuditRepository(db)
    email_service = EmailService()
    return AuthService(user_repo, audit_repo, email_service)


# ---------------------------------------------------------------------------
# Public endpoints (no token required)
# ---------------------------------------------------------------------------

@router.post(
    "/register-request",
    response_model=RegisterRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit an account signup request",
    description=(
        "Public endpoint — no authentication required. "
        "Allows anyone to submit a request to create an account. "
        "The request is stored with status `pending` and all active admins are "
        "notified by email. An admin must then approve or reject the request via "
        "`POST /admin/account-requests/{id}/approve` or `.../reject`. "
        "Returns the ID of the created request so applicants can reference it."
    ),
)
async def register_request(
    request: Request,
    body: RegisterRequest,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    request_id = await auth_service.process_register_request(body, ip_address, background_tasks)
    return RegisterRequestResponse(request_id=request_id)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and obtain a JWT access token",
    description=(
        "Validates the provided email and password against stored credentials. "
        "On success, returns a signed JWT Bearer token and its expiry duration in seconds. "
        "The `must_change_password` flag indicates if the user should be redirected to "
        "`POST /auth/change-password` before continuing — this is set when an admin "
        "creates or resets the account. "
        "Failed login attempts are recorded in the audit log."
    ),
)
async def login(
    request: Request,
    body: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    user = await auth_service.authenticate_user(body, ip_address)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return TokenResponse(
        access_token=create_access_token(user.email, expires_delta=access_token_expires),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        must_change_password=user.must_change_password,
    )


# ---------------------------------------------------------------------------
# Authenticated endpoints (JWT required)
# ---------------------------------------------------------------------------

@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Log out the current user",
    description=(
        "Records a logout event in the audit log for the currently authenticated user. "
        "Since JWTs are stateless, the token itself is not invalidated server-side — "
        "the client is responsible for discarding it. "
        "The logout event timestamp can be used for session audit trails."
    ),
)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    await auth_service.record_logout(current_user, ip_address)
    return LogoutResponse()


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change the current user's password",
    description=(
        "Allows the authenticated user to update their own password. "
        "Requires the current password for verification before the new one is accepted. "
        "After a successful change, the `must_change_password` flag is cleared, "
        "allowing the user to access all other endpoints normally. "
        "This endpoint must be called before accessing other routes if "
        "`must_change_password` is `true` in the login response."
    ),
)
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    await auth_service.change_password(current_user, body, ip_address)
    return {"message": "Password changed successfully"}
