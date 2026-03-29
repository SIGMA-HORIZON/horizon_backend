"""
Admin Endpoints — /api/v1/admin

All routes in this module are restricted to users with the ADMIN role.
Admins manage the full user lifecycle: reviewing signup requests,
creating accounts, updating roles, suspending/restoring access, and
forcing password resets.

Access control: JWT Bearer token required + role must be ADMIN.
"""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Request, status, Query, BackgroundTasks, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.api.deps import get_current_admin
from app.schemas.admin import (
    AccountRequestResponse,
    ApproveRequest,
    ApproveResponse,
    RejectRequest,
    UserCreate,
    UserResponse,
    UserUpdate,
    DeactivateRequest,
    DeactivateResponse,
)
from app.services.admin_service import AdminService
from app.repositories.user_repository import UserRepository
from app.repositories.account_request_repository import AccountRequestRepository
from app.repositories.audit_repository import AuditRepository
from app.services.email_service import EmailService
from app.models.enums import AccountRequestStatus, RoleType
from app.models.base_models import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

async def get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminService:
    """Construct AdminService with all required repositories injected."""
    user_repo = UserRepository(db)
    request_repo = AccountRequestRepository(db)
    audit_repo = AuditRepository(db)
    email_service = EmailService()
    return AdminService(user_repo, request_repo, audit_repo, email_service)


# ---------------------------------------------------------------------------
# Account Request endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/account-requests",
    response_model=List[AccountRequestResponse],
    summary="List account signup requests",
    description=(
        "Returns all account requests submitted through the public registration form. "
        "Optionally filter by status: `pending`, `approved`, or `rejected`. "
        "Use this to review who is waiting to be on-boarded."
    ),
)
async def list_account_requests(
    status: Optional[AccountRequestStatus] = Query(
        None,
        description="Filter by request status. Omit to return all."
    ),
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    return await admin_service.list_account_requests(status_filter=status)


@router.post(
    "/account-requests/{request_id}/approve",
    response_model=ApproveResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve an account request",
    description=(
        "Approves a pending signup request and automatically creates a user account. "
        "A provisional password is generated and emailed to the applicant. "
        "The user will be required to change their password on first login. "
        "The action is recorded in the audit log."
    ),
)
async def approve_account_request(
    request: Request,
    request_id: uuid.UUID,
    body: ApproveRequest,
    background_tasks: BackgroundTasks,
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    user = await admin_service.approve_request(request_id, body, admin, ip_address, background_tasks)
    return ApproveResponse(user_id=user.id, username=user.username, email_sent=True)


@router.post(
    "/account-requests/{request_id}/reject",
    status_code=status.HTTP_200_OK,
    summary="Reject an account request",
    description=(
        "Rejects a pending signup request. An optional rejection reason can be provided "
        "and will be included in the notification email sent to the applicant. "
        "The action is recorded in the audit log."
    ),
)
async def reject_account_request(
    request: Request,
    request_id: uuid.UUID,
    body: RejectRequest,
    background_tasks: BackgroundTasks,
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    await admin_service.reject_request(request_id, body.reason, admin, ip_address, background_tasks)
    return {"message": "Request rejected successfully"}


# ---------------------------------------------------------------------------
# User management endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/users",
    response_model=ApproveResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user account directly",
    description=(
        "Allows an admin to create a user account without going through the signup request flow. "
        "Useful for on-boarding staff or testing. A provisional password is auto-generated "
        "and emailed to the new user. They must change it on first login."
    ),
)
async def create_user(
    request: Request,
    body: UserCreate,
    background_tasks: BackgroundTasks,
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    user = await admin_service.create_user_manually(body, admin, ip_address, background_tasks)
    return ApproveResponse(user_id=user.id, username=user.username, email_sent=True)


@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="List all users",
    description=(
        "Returns a paginated list of all registered users. "
        "Supports optional filters: `is_active` (true/false), `role` (user/admin), "
        "and `search` (matches against email, first name, or last name)."
    ),
)
async def list_users(
    is_active: Optional[bool] = Query(None, description="Filter by active/inactive status."),
    role: Optional[RoleType] = Query(None, description="Filter by role type: user or admin."),
    search: Optional[str] = Query(None, description="Search by name or email (case-insensitive)."),
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    return await admin_service.list_users(is_active=is_active, role=role, search=search)


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get a single user by ID",
    description=(
        "Fetches the full profile of a specific user by their UUID. "
        "Returns 404 if no user with the given ID exists."
    ),
)
async def get_user(
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).options(joinedload(User.role)).where(User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.role_type,
        "is_active": user.is_active,
        "last_login": user.last_login,
    }


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update a user's role or email",
    description=(
        "Allows an admin to update a user's email address or reassign their role. "
        "All changes are recorded in the audit log. "
        "Note: changing the email also updates the username since they are kept in sync."
    ),
)
async def update_user(
    request: Request,
    user_id: uuid.UUID,
    body: UserUpdate,
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    return await admin_service.update_user(user_id, body, admin, ip_address)


@router.post(
    "/users/{user_id}/deactivate",
    response_model=DeactivateResponse,
    summary="Deactivate (suspend) a user account",
    description=(
        "Marks a user account as inactive and records the suspension timestamp. "
        "The user will immediately lose the ability to log in or use the API. "
        "An optional reason can be provided for audit purposes. "
        "The account can be restored using the `/reactivate` endpoint."
    ),
)
async def deactivate_user(
    request: Request,
    user_id: uuid.UUID,
    body: DeactivateRequest,
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    user = await admin_service.deactivate_user(user_id, body.reason, admin, ip_address)
    return DeactivateResponse(message="Account deactivated", suspended_at=user.suspended_at)


@router.post(
    "/users/{user_id}/reactivate",
    status_code=status.HTTP_200_OK,
    summary="Reactivate a suspended user account",
    description=(
        "Restores a previously deactivated user account. "
        "The user regains the ability to log in immediately. "
        "The suspension timestamp is cleared and the action is audit-logged."
    ),
)
async def reactivate_user(
    request: Request,
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    await admin_service.reactivate_user(user_id, admin, ip_address)
    return {"message": "Account reactivated"}


@router.post(
    "/users/{user_id}/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Force a password reset for a user",
    description=(
        "Generates a new random provisional password for the specified user and emails it to them. "
        "The user's `must_change_password` flag is set to `true`, forcing them to choose a new "
        "password the next time they log in via `POST /auth/change-password`. "
        "Use this when a user is locked out, forgets their password, or their account is suspected compromised. "
        "The action is recorded in the audit log."
    ),
)
async def reset_password(
    request: Request,
    user_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    email_sent = await admin_service.reset_password(user_id, admin, ip_address, background_tasks)
    return {"email_sent": email_sent, "message": "Password reset successfully"}
