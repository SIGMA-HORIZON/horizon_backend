"""Routes /api/v1/accounts."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from horizon.features.accounts import schemas
from horizon.features.accounts import service as account_service
from horizon.infrastructure.database import get_db
from horizon.shared.dependencies import AdminUser
from horizon.shared.models import AccountRequest, AccountRequestStatus, AuditAction, User, UserRoleEnum
from horizon.shared.audit_service import log_action
from horizon.shared.policies.enforcer import PolicyError
from horizon.shared.schemas.common import MessageResponse

router = APIRouter(prefix="/accounts", tags=["Comptes"])


@router.post(
    "/request",
    response_model=schemas.AccountRequestResponse,
    status_code=201,
    summary="Soumettre une demande de compte (public)",
)
def submit_request(body: schemas.AccountRequestCreate, db: Session = Depends(get_db)):
    req = account_service.submit_account_request(db, body.model_dump())
    return req


@router.get(
    "/requests",
    response_model=schemas.AccountRequestListResponse,
    summary="[Admin] Liste des demandes",
)
def list_requests(
    admin: AdminUser,
    status: str = Query("PENDING"),
    db: Session = Depends(get_db),
):
    q = db.query(AccountRequest)
    if status:
        q = q.filter(AccountRequest.status == AccountRequestStatus(status))
    rows = q.order_by(AccountRequest.created_at.desc()).all()
    return schemas.AccountRequestListResponse(
        items=[schemas.AccountRequestResponse.model_validate(r) for r in rows]
    )


@router.post(
    "/requests/{request_id}/approve",
    response_model=schemas.ApproveAccountResponse,
    summary="[Admin] Approuver une demande de compte",
)
def approve_request(
    request_id: uuid.UUID,
    body: schemas.ApproveRequestBody,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    user, _ = account_service.approve_account_request(
        db, request_id, admin.id, body.quota_policy_id
    )
    return schemas.ApproveAccountResponse(
        message=f"Compte créé pour {user.email}.",
        username=user.username,
    )


@router.post(
    "/requests/{request_id}/reject",
    response_model=MessageResponse,
    summary="[Admin] Rejeter une demande de compte",
)
def reject_request(
    request_id: uuid.UUID,
    body: schemas.RejectRequestBody,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    account_service.reject_account_request(db, request_id, admin.id, body.reason)
    return MessageResponse(message="Demande rejetée.")


@router.post(
    "",
    response_model=schemas.UserResponse,
    status_code=201,
    summary="[Admin] Créer un compte directement",
)
def create_user(body: schemas.AdminCreateUser, admin: AdminUser, db: Session = Depends(get_db)):
    user, _ = account_service.admin_create_user(db, body.model_dump(), admin.id)
    return user


@router.get(
    "",
    response_model=schemas.UserListResponse,
    summary="[Admin] Liste de tous les utilisateurs",
)
def list_users(admin: AdminUser, db: Session = Depends(get_db)):
    rows = db.query(User).order_by(User.created_at.desc()).all()
    return schemas.UserListResponse(
        items=[schemas.UserResponse.model_validate(u) for u in rows]
    )


@router.get(
    "/{user_id}",
    response_model=schemas.UserResponse,
    summary="[Admin] Détail d'un utilisateur",
)
def get_user(user_id: uuid.UUID, admin: AdminUser, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise PolicyError("ACCOUNT", "Utilisateur introuvable.", 404)
    return user


@router.patch(
    "/{user_id}",
    response_model=schemas.UserResponse,
    summary="[Admin] Modifier un compte",
)
def update_user(
    user_id: uuid.UUID,
    body: schemas.AdminUpdateUser,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise PolicyError("ACCOUNT", "Utilisateur introuvable.", 404)
    data = body.model_dump(exclude_none=True)
    for k, v in data.items():
        if k == "role":
            setattr(user, k, UserRoleEnum(v))
        elif k == "quota_policy_id" and v is not None:
            setattr(user, k, uuid.UUID(v))
        else:
            setattr(user, k, v)
    log_action(db, admin.id, AuditAction.ACCOUNT_APPROVED, "user", user.id)
    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/{user_id}/suspend",
    response_model=MessageResponse,
    summary="[Admin] Suspendre un compte",
)
def suspend_user(user_id: uuid.UUID, admin: AdminUser, db: Session = Depends(get_db)):
    account_service.suspend_user(db, user_id, admin.id)
    return MessageResponse(message="Compte suspendu.")


@router.post(
    "/{user_id}/reactivate",
    response_model=MessageResponse,
    summary="[Admin] Réactiver un compte",
)
def reactivate_user(user_id: uuid.UUID, admin: AdminUser, db: Session = Depends(get_db)):
    account_service.reactivate_user(db, user_id, admin.id)
    return MessageResponse(message="Compte réactivé.")


@router.post(
    "/{user_id}/reset-password",
    response_model=MessageResponse,
    summary="[Admin] Réinitialiser le mot de passe",
)
def reset_password(user_id: uuid.UUID, admin: AdminUser, db: Session = Depends(get_db)):
    account_service.reset_user_password(db, user_id, admin.id)
    return MessageResponse(message="Nouveau mot de passe envoyé par e-mail.")
