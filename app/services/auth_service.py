import uuid
from typing import List, Optional
from fastapi import HTTPException, status, BackgroundTasks
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository
from app.services.email_service import EmailService
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, ChangePasswordRequest
from app.models.base_models import AuditLog, User, AccountRequest
from app.models.enums import ActionType, AccountRequestStatus
from app.core.security import verify_password, create_access_token, get_password_hash

class AuthService:
    def __init__(
        self, 
        user_repo: UserRepository, 
        audit_repo: AuditRepository,
        email_service: EmailService
    ):
        self.user_repo = user_repo
        self.audit_repo = audit_repo
        self.email_service = email_service

    async def process_register_request(self, register_in: RegisterRequest, ip_address: str, background_tasks: BackgroundTasks) -> str:
        # 1. Check if email already exists in users table
        existing_user = await self.user_repo.get_by_email(register_in.email)
        if existing_user:
            # ... (logged error)
            audit_log = AuditLog(
                action_type=ActionType.LOGIN_FAILED,
                description=f"Account creation request failed for {register_in.email} (Email already exists)",
                success=False,
                ip_address=ip_address
            )
            await self.audit_repo.create(audit_log)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered."
            )

        # 2. Persist the account request
        new_request = AccountRequest(
            email=register_in.email,
            first_name=register_in.first_name,
            last_name=register_in.last_name,
            organisation=register_in.organisation,
            justification=register_in.justification,
            status=AccountRequestStatus.PENDING
        )
        self.user_repo.db.add(new_request)
        await self.user_repo.db.commit()
        await self.user_repo.db.refresh(new_request)

        # 3. Log the action (Audit)
        audit_log = AuditLog(
            action_type=ActionType.LOGIN,
            description=f"Account creation request submitted for {register_in.email} (Request ID: {new_request.id})",
            success=True,
            ip_address=ip_address
        )
        await self.audit_repo.create(audit_log)

        # 4. Get active admins
        admins = await self.user_repo.get_active_admins()
        admin_emails = [admin.email for admin in admins]

        # 5. Send email to admins (background)
        background_tasks.add_task(
            self.email_service.send_new_account_request_email,
            admin_emails=admin_emails,
            request_data=register_in.model_dump(),
            request_id=str(new_request.id)
        )

        return str(new_request.id)

    async def authenticate_user(self, login_in: LoginRequest, ip_address: str) -> User:
        user = await self.user_repo.get_by_email(login_in.email)
        
        if not user or not verify_password(login_in.password, user.password_hash) or not user.is_active:
            audit_log = AuditLog(
                action_type=ActionType.LOGIN_FAILED,
                description=f"Login failed for email: {login_in.email}",
                success=False,
                ip_address=ip_address
            )
            await self.audit_repo.create(audit_log)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        audit_log = AuditLog(
            user_id=user.id,
            action_type=ActionType.LOGIN,
            description=f"User {user.email} logged in successfully",
            success=True,
            ip_address=ip_address
        )
        await self.audit_repo.create(audit_log)
        return user

    async def change_password(self, user: User, change_in: ChangePasswordRequest, ip_address: str) -> None:
        if not verify_password(change_in.current_password, user.password_hash):
            audit_log = AuditLog(
                user_id=user.id,
                action_type=ActionType.ADMIN_ACCOUNT_MODIFY,
                description="Failed password change: Incorrect current password",
                success=False,
                ip_address=ip_address
            )
            await self.audit_repo.create(audit_log)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        if change_in.new_password != change_in.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
        
        user.password_hash = get_password_hash(change_in.new_password)
        user.must_change_password = False
        await self.user_repo.update(user)
        
        audit_log = AuditLog(
            user_id=user.id,
            action_type=ActionType.ADMIN_ACCOUNT_MODIFY,
            description="Password changed successfully",
            success=True,
            ip_address=ip_address
        )
        await self.audit_repo.create(audit_log)

    async def record_logout(self, user: User, ip_address: str) -> None:
        audit_log = AuditLog(
            user_id=user.id,
            action_type=ActionType.LOGOUT,
            description=f"User {user.username} logged out",
            success=True,
            ip_address=ip_address
        )
        await self.audit_repo.create(audit_log)
