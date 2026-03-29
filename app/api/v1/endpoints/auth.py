from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.schemas.auth import RegisterRequest, RegisterRequestResponse
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository
from app.services.email_service import EmailService
from app.services.auth_service import AuthService

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
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Submits a registration request, logs the attempt, and notifies admins.
    """
    ip_address = request.client.host if request.client else "0.0.0.0"
    request_id = await auth_service.process_register_request(body, ip_address)
    
    return RegisterRequestResponse(request_id=request_id)
