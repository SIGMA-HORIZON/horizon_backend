import secrets
import string
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status, BackgroundTasks
from app.repositories.user_repository import UserRepository
from app.repositories.account_request_repository import AccountRequestRepository
from app.repositories.audit_repository import AuditRepository
from app.services.email_service import EmailService
from app.models.base_models import User, AccountRequest, AuditLog, Role
from app.models.enums import RoleType, AccountRequestStatus, ActionType
from app.core.security import get_password_hash
from app.schemas.admin import UserCreate, UserUpdate, ApproveRequest

class AdminService:
    def __init__(
        self,
        user_repo: UserRepository,
        request_repo: AccountRequestRepository,
        audit_repo: AuditRepository,
        email_service: EmailService
    ):
        self.user_repo = user_repo
        self.request_repo = request_repo
        self.audit_repo = audit_repo
        self.email_service = email_service

    def _generate_provisional_password(self, length: int = 12) -> str:
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    async def list_account_requests(self, status_filter: Optional[AccountRequestStatus] = None) -> List[AccountRequest]:
        return await self.request_repo.list_requests(status=status_filter)

    async def approve_request(self, request_id: uuid.UUID, approve_in: ApproveRequest, admin: User, ip_address: str, background_tasks: BackgroundTasks) -> User:
        request = await self.request_repo.get_by_id(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        if request.status != AccountRequestStatus.PENDING:
            raise HTTPException(status_code=400, detail="Request already processed")

        # Create user
        provisional_password = self._generate_provisional_password()
        
        from app.models.base_models import Role
        from sqlalchemy import select
        res = await self.user_repo.db.execute(select(Role).where(Role.role_type == approve_in.role))
        role = res.scalars().first()
        
        user = User(
            username=request.email, # Using email as username as requested earlier
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            password_hash=get_password_hash(provisional_password),
            role_id=role.id,
            is_active=True,
            must_change_password=True
        )
        
        await self.user_repo.create(user)
        
        # Update request
        request.status = AccountRequestStatus.APPROVED
        request.processed_at = datetime.now(timezone.utc)
        request.processed_by = admin.id
        await self.request_repo.update(request)
        
        # Audit
        audit_log = AuditLog(
            user_id=admin.id,
            action_type=ActionType.ADMIN_ACCOUNT_CREATE,
            description=f"Approved request {request_id} for {request.email}",
            success=True,
            ip_address=ip_address
        )
        await self.audit_repo.create(audit_log)
        
        # Email (background)
        background_tasks.add_task(self.email_service.send_account_approved_email, user.email, provisional_password)
        
        return user

    async def reject_request(self, request_id: uuid.UUID, reason: Optional[str], admin: User, ip_address: str, background_tasks: BackgroundTasks) -> None:
        request = await self.request_repo.get_by_id(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        if request.status != AccountRequestStatus.PENDING:
            raise HTTPException(status_code=400, detail="Request already processed")

        request.status = AccountRequestStatus.REJECTED
        request.processed_at = datetime.now(timezone.utc)
        request.processed_by = admin.id
        request.rejection_reason = reason
        await self.request_repo.update(request)
        
        # Audit
        audit_log = AuditLog(
            user_id=admin.id,
            action_type=ActionType.ADMIN_ACCOUNT_MODIFY,
            description=f"Rejected request {request_id} for {request.email}. Reason: {reason}",
            success=True,
            ip_address=ip_address
        )
        await self.audit_repo.create(audit_log)
        
        background_tasks.add_task(self.email_service.send_account_rejected_email, request.email, reason)

    async def create_user_manually(self, user_in: UserCreate, admin: User, ip_address: str, background_tasks: BackgroundTasks) -> User:
        existing = await self.user_repo.get_by_email(user_in.email)
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
            
        provisional_password = self._generate_provisional_password()
        
        from sqlalchemy import select
        res = await self.user_repo.db.execute(select(Role).where(Role.role_type == user_in.role))
        role = res.scalars().first()
        
        user = User(
            username=user_in.email,
            email=user_in.email,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            password_hash=get_password_hash(provisional_password),
            role_id=role.id,
            is_active=True,
            must_change_password=True
        )
        
        await self.user_repo.create(user)
        
        # Audit
        audit_log = AuditLog(
            user_id=admin.id,
            action_type=ActionType.ADMIN_ACCOUNT_CREATE,
            description=f"Manually created user {user.email}",
            success=True,
            ip_address=ip_address
        )
        await self.audit_repo.create(audit_log)
        
        background_tasks.add_task(self.email_service.send_account_approved_email, user.email, provisional_password)
        return user

    async def list_users(self, is_active: Optional[bool] = None, role: Optional[RoleType] = None, search: Optional[str] = None) -> List[dict]:
        from sqlalchemy import select, or_
        from sqlalchemy.orm import joinedload
        query = select(User).join(Role).options(joinedload(User.role))
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if role:
            query = query.where(Role.role_type == role)
        if search:
            query = query.where(or_(
                User.email.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%")
            ))
        
        result = await self.user_repo.db.execute(query)
        users = result.scalars().all()
        
        return [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role.role_type,
                "is_active": u.is_active,
                "last_login": u.last_login
            } for u in users
        ]

    async def deactivate_user(self, user_id: uuid.UUID, reason: Optional[str], admin: User, ip_address: str) -> User:
        # Generic get by id in UserRepository
        from sqlalchemy import select
        res = await self.user_repo.db.execute(select(User).where(User.id == user_id))
        user = res.scalars().first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_active = False
        user.suspended_at = datetime.now(timezone.utc)
        await self.user_repo.update(user)
        
        # Audit
        audit_log = AuditLog(
            user_id=admin.id,
            action_type=ActionType.ADMIN_ACCOUNT_SUSPEND,
            description=f"Deactivated user {user.email}. Reason: {reason}",
            success=True,
            ip_address=ip_address
        )
        await self.audit_repo.create(audit_log)
        
        return user

    async def reactivate_user(self, user_id: uuid.UUID, admin: User, ip_address: str) -> User:
        from sqlalchemy import select
        res = await self.user_repo.db.execute(select(User).where(User.id == user_id))
        user = res.scalars().first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_active = True
        user.suspended_at = None
        await self.user_repo.update(user)
        
        # Audit
        audit_log = AuditLog(
            user_id=admin.id,
            action_type=ActionType.ADMIN_ACCOUNT_MODIFY,
            description=f"Reactivated user {user.email}",
            success=True,
            ip_address=ip_address
        )
        await self.audit_repo.create(audit_log)
        
        return user

    async def reset_password(self, user_id: uuid.UUID, admin: User, ip_address: str, background_tasks: BackgroundTasks) -> bool:
        from sqlalchemy import select
        res = await self.user_repo.db.execute(select(User).where(User.id == user_id))
        user = res.scalars().first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        provisional_password = self._generate_provisional_password()
        user.password_hash = get_password_hash(provisional_password)
        user.must_change_password = True
        await self.user_repo.update(user)
        
        # Audit
        audit_log = AuditLog(
            user_id=admin.id,
            action_type=ActionType.ADMIN_ACCOUNT_MODIFY,
            description=f"Reset password for user {user.email}",
            success=True,
            ip_address=ip_address
        )
        await self.audit_repo.create(audit_log)
        
        background_tasks.add_task(self.email_service.send_password_reset_email, user.email, provisional_password)
        return True

    async def update_user(self, user_id: uuid.UUID, user_update: UserUpdate, admin: User, ip_address: str) -> User:
        from sqlalchemy import select
        res = await self.user_repo.db.execute(select(User).where(User.id == user_id))
        user = res.scalars().first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        updated_fields = []
        if user_update.email:
            user.email = user_update.email
            user.username = user_update.email
            updated_fields.append("email")
        if user_update.role:
            res = await self.user_repo.db.execute(select(Role).where(Role.role_type == user_update.role))
            role = res.scalars().first()
            user.role_id = role.id
            updated_fields.append("role")
        
        if updated_fields:
            await self.user_repo.update(user)
            # Audit
            audit_log = AuditLog(
                user_id=admin.id,
                action_type=ActionType.ADMIN_ACCOUNT_MODIFY,
                description=f"Updated user {user.email}: {', '.join(updated_fields)}",
                success=True,
                ip_address=ip_address
            )
            await self.audit_repo.create(audit_log)
            
        return user
