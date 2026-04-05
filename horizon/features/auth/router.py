"""Routes /api/v1/auth."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from horizon.features.auth import schemas
from horizon.features.auth import service as auth_service
from horizon.infrastructure.database import get_db
from horizon.shared.dependencies import CurrentUser
from horizon.shared.schemas.common import MessageResponse

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/login", response_model=schemas.TokenResponse, summary="Connexion utilisateur")
def login(body: schemas.LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    user = auth_service.authenticate_user(db, body.username, body.password, ip)
    token = auth_service.create_access_token(
        str(user.id), user.role.value, user.must_change_pwd
    )
    return schemas.TokenResponse(
        access_token=token,
        must_change_pwd=user.must_change_pwd,
        role=user.role.value,
    )


@router.patch(
    "/change-password",
    response_model=MessageResponse,
    summary="Changer le mot de passe",
)
def change_password(
    body: schemas.ChangePasswordRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    auth_service.change_password(
        db, current_user.id, body.current_password, body.new_password
    )
    return MessageResponse(message="Mot de passe changé avec succès.")


@router.get("/me", response_model=schemas.UserResponse, summary="Profil utilisateur connecté")
def get_me(current_user: CurrentUser):
    return current_user
