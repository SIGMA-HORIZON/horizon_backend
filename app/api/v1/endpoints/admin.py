from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Request, status, Query, BackgroundTasks
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
    DeactivateResponse
)
from app.services.admin_service import AdminService
from app.repositories.user_repository import UserRepository
from app.repositories.account_request_repository import AccountRequestRepository
from app.repositories.audit_repository import AuditRepository
from app.services.email_service import EmailService
from app.models.enums import AccountRequestStatus, RoleType
from app.models.base_models import User

router = APIRouter()

async def get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminService:
    user_repo = UserRepository(db)
    request_repo = AccountRequestRepository(db)
    audit_repo = AuditRepository(db)
    email_service = EmailService()
    return AdminService(user_repo, request_repo, audit_repo, email_service)

@router.get("/account-requests", response_model=List[AccountRequestResponse])
async def list_account_requests(
    status: Optional[AccountRequestStatus] = Query(None),
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
):
    return await admin_service.list_account_requests(status_filter=status)

@router.post("/account-requests/{request_id}/approve", response_model=ApproveResponse)
async def approve_account_request(
    request: Request,
    request_id: uuid.UUID,
    body: ApproveRequest,
    background_tasks: BackgroundTasks,
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    user = await admin_service.approve_request(request_id, body, admin, ip_address, background_tasks)
    return ApproveResponse(user_id=user.id, username=user.username, email_sent=True)

@router.post("/account-requests/{request_id}/reject")
async def reject_account_request(
    request: Request,
    request_id: uuid.UUID,
    body: RejectRequest,
    background_tasks: BackgroundTasks,
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    await admin_service.reject_request(request_id, body.reason, admin, ip_address, background_tasks)
    return {"message": "Request rejected successfully"}

@router.post("/users", response_model=ApproveResponse)
async def create_user(
    request: Request,
    body: UserCreate,
    background_tasks: BackgroundTasks,
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    user = await admin_service.create_user_manually(body, admin, ip_address, background_tasks)
    return ApproveResponse(user_id=user.id, username=user.username, email_sent=True)

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    is_active: Optional[bool] = Query(None),
    role: Optional[RoleType] = Query(None),
    search: Optional[str] = Query(None),
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
):
    return await admin_service.list_users(is_active=is_active, role=role, search=search)

@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: uuid.UUID,
    body: UserUpdate,
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    return await admin_service.update_user(user_id, body, admin, ip_address)

@router.post("/users/{user_id}/deactivate", response_model=DeactivateResponse)
async def deactivate_user(
    request: Request,
    user_id: uuid.UUID,
    body: DeactivateRequest,
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    user = await admin_service.deactivate_user(user_id, body.reason, admin, ip_address)
    return DeactivateResponse(message="Account deactivated", suspended_at=user.suspended_at)

@router.post("/users/{user_id}/reactivate")
async def reactivate_user(
    request: Request,
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    await admin_service.reactivate_user(user_id, admin, ip_address)
    return {"message": "Account reactivated"}

@router.post("/users/{user_id}/reset-password")
async def reset_password(
    request: Request,
    user_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    email_sent = await admin_service.reset_password(user_id, admin, ip_address, background_tasks)
    return {"email_sent": email_sent, "message": "Password reset successfully"}
