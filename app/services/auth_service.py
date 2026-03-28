import uuid
from typing import Optional
from fastapi import HTTPException, status
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository
from app.services.email_service import EmailService
from app.schemas.auth import RegisterRequest
from app.models.base_models import AuditLog, User
from app.models.enums import ActionType

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

    async def process_register_request(self, register_in: RegisterRequest, ip_address: str) -> str:
        """
        Logic for processing a registration request.
        """
        # 1. Check if email already exists in users table
        existing_user = await self.user_repo.get_by_email(register_in.email)
        if existing_user:
            # Create a failed audit log (closest action_type: login_failed)
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

        # 2. Generate request_id
        request_id = str(uuid.uuid4())

        # 3. Log the action (Audit)
        # Using ActionType.LOGIN as instructed for closest match
        audit_log = AuditLog(
            action_type=ActionType.LOGIN,
            description=f"Account creation request submitted for {register_in.email}",
            success=True,
            ip_address=ip_address
        )
        await self.audit_repo.create(audit_log)

        # 4. Get active admins
        admins = await self.user_repo.get_active_admins()
        admin_emails = [admin.email for admin in admins]

        # 5. Send email to admins (async, silent failure)
        await self.email_service.send_new_account_request_email(
            admin_emails=admin_emails,
            request_data=register_in.model_dump(),
            request_id=request_id
        )

        return request_id
