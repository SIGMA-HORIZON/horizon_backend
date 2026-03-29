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
    ChangePasswordRequest
)
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository
from app.services.email_service import EmailService
from app.services.auth_service import AuthService
from app.core.security import create_access_token
from app.core.config import settings
from app.models.base_models import User

router = APIRouter()

async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """
    Dependency injection for AuthService.
    """
    user_repo = UserRepository(db)
    audit_repo = AuditRepository(db)
    email_service = EmailService()
    return AuthService(user_repo, audit_repo, email_service)

@router.post(
    "/register-request", 
    response_model=RegisterRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit an account creation request",
    description="Public endpoint to request account creation. Notifies admins via email."
)
async def register_request(
    request: Request,
    body: RegisterRequest,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Submits a registration request, logs the attempt, and notifies admins.
    """
    ip_address = request.client.host if request.client else "0.0.0.0"
    request_id = await auth_service.process_register_request(body, ip_address, background_tasks)
    
    return RegisterRequestResponse(request_id=request_id)

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and obtain JWT token",
)
async def login(
    request: Request,
    body: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    user = await auth_service.authenticate_user(body, ip_address)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return TokenResponse(
        access_token=create_access_token(
            user.email, expires_delta=access_token_expires
        ),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        must_change_password=user.must_change_password
    )

@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Log out the current user"
)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    await auth_service.record_logout(current_user, ip_address)
    return LogoutResponse()

@router.post(
    "/change-password",
    summary="Change the current user's password"
)
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    ip_address = request.client.host if request.client else "0.0.0.0"
    await auth_service.change_password(current_user, body, ip_address)
    return {"message": "Password changed successfully"}
