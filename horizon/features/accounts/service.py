"""Cycle de vie des comptes (POL-COMPTE-01/02/03)."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from horizon.core.config import get_settings
from horizon.features.auth.service import generate_temp_password, hash_password
from horizon.infrastructure.email_service import (
    send_account_credentials,
    send_account_rejected,
    send_account_request_received,
    send_admin_new_request,
)
from horizon.shared.audit_service import log_action
from horizon.shared.models import (
    AccountRequest,
    AccountRequestStatus,
    AuditAction,
    User,
    UserRoleEnum,
)
from horizon.shared.policies.enforcer import PolicyError

settings = get_settings()


def submit_account_request(db: Session, data: dict) -> AccountRequest:
    existing = db.query(AccountRequest).filter(AccountRequest.email == data["email"]).first()
    if existing:
        raise PolicyError(
            "POL-COMPTE-01",
            "Une demande existe déjà pour cette adresse e-mail.",
            409,
        )

    req = AccountRequest(
        id=uuid.uuid4(),
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data["email"],
        organisation=data["organisation"],
        justification=data.get("justification"),
        status=AccountRequestStatus.PENDING,
    )
    db.add(req)

    log_action(db, None, AuditAction.ACCOUNT_REQUEST_SUBMITTED, "account_request", req.id)
    db.commit()
    db.refresh(req)

    send_account_request_received(req.email, req.first_name)
    admin_emails = _get_admin_emails(db)
    send_admin_new_request(admin_emails, req.first_name, req.last_name, req.organisation)

    return req


def approve_account_request(
    db: Session,
    request_id: uuid.UUID,
    admin_id,
    quota_policy_id: Optional[str] = None,
) -> tuple[User, str]:
    req = db.query(AccountRequest).filter(AccountRequest.id == request_id).first()
    if not req:
        raise PolicyError("POL-COMPTE-01", "Demande introuvable.", 404)
    if req.status != AccountRequestStatus.PENDING:
        raise PolicyError("POL-COMPTE-01", f"Cette demande est déjà '{req.status}'.", 409)

    existing_user = db.query(User).filter(User.email == req.email).first()
    if existing_user:
        raise PolicyError("POL-COMPTE-01", "Un compte avec cet e-mail existe déjà.", 409)

    temp_pwd = generate_temp_password()
    username = _generate_username(db, req.first_name, req.last_name)

    valid_quota_id = None
    if quota_policy_id and quota_policy_id not in ("null", "undefined", "None", ""):
        valid_quota_id = uuid.UUID(quota_policy_id)

    user = User(
        id=uuid.uuid4(),
        username=username,
        email=req.email,
        hashed_password=hash_password(temp_pwd),
        first_name=req.first_name,
        last_name=req.last_name,
        organisation=req.organisation,
        must_change_pwd=True,
        is_active=True,
        quota_policy_id=valid_quota_id,
    )
    db.add(user)

    req.status = AccountRequestStatus.APPROVED
    req.reviewed_by_id = admin_id
    req.reviewed_at = datetime.now(timezone.utc).isoformat()
    req.user_id = user.id

    log_action(
        db,
        admin_id,
        AuditAction.ACCOUNT_APPROVED,
        "user",
        user.id,
        metadata={"request_id": str(request_id)},
    )
    db.commit()
    db.refresh(user)

    send_account_credentials(user.email, username, temp_pwd)
    return user, temp_pwd


def reject_account_request(db: Session, request_id: uuid.UUID, admin_id, reason: str) -> None:
    req = db.query(AccountRequest).filter(AccountRequest.id == request_id).first()
    if not req:
        raise PolicyError("POL-COMPTE-01", "Demande introuvable.", 404)
    if req.status != AccountRequestStatus.PENDING:
        raise PolicyError("POL-COMPTE-01", "Cette demande n'est plus en attente.", 409)

    req.status = AccountRequestStatus.REJECTED
    req.reviewed_by_id = admin_id
    req.reviewed_at = datetime.now(timezone.utc).isoformat()
    req.rejection_reason = reason

    log_action(
        db,
        admin_id,
        AuditAction.ACCOUNT_REJECTED,
        "account_request",
        req.id,
        metadata={"reason": reason},
    )
    db.commit()

    send_account_rejected(req.email, req.first_name, reason)


def admin_create_user(db: Session, data: dict, admin_id) -> tuple[User, str]:
    existing = db.query(User).filter(User.email == data["email"]).first()
    if existing:
        raise PolicyError("POL-COMPTE-01", "Un compte avec cet e-mail existe déjà.", 409)

    temp_pwd = generate_temp_password()
    username = _generate_username(db, data["first_name"], data["last_name"])

    user = User(
        id=uuid.uuid4(),
        username=username,
        email=data["email"],
        hashed_password=hash_password(temp_pwd),
        first_name=data["first_name"],
        last_name=data["last_name"],
        organisation=data.get("organisation"),
        role=UserRoleEnum(data.get("role", "USER")),
        must_change_pwd=True,
        is_active=True,
        quota_policy_id=uuid.UUID(data["quota_policy_id"]) if data.get("quota_policy_id") else None,
    )
    db.add(user)
    log_action(db, admin_id, AuditAction.ACCOUNT_APPROVED, "user", user.id)
    db.commit()
    db.refresh(user)

    send_account_credentials(user.email, username, temp_pwd)
    return user, temp_pwd


def suspend_user(db: Session, user_id, admin_id, reason: str = "Violation de politique") -> None:
    user = _get_user_or_404(db, user_id)
    user.is_active = False
    log_action(
        db,
        admin_id,
        AuditAction.ACCOUNT_SUSPENDED,
        "user",
        user.id,
        metadata={"reason": reason},
    )
    db.commit()


def reactivate_user(db: Session, user_id, admin_id) -> None:
    user = _get_user_or_404(db, user_id)
    user.is_active = True
    user.failed_login_count = 0
    user.locked_until = None
    log_action(db, admin_id, AuditAction.ACCOUNT_REACTIVATED, "user", user.id)
    db.commit()


def reset_user_password(db: Session, user_id, admin_id) -> str:
    user = _get_user_or_404(db, user_id)
    temp_pwd = generate_temp_password()
    user.hashed_password = hash_password(temp_pwd)
    user.must_change_pwd = True
    log_action(db, admin_id, AuditAction.PASSWORD_RESET, "user", user.id)
    db.commit()
    send_account_credentials(user.email, user.username, temp_pwd)
    return temp_pwd


def _generate_username(db: Session, first_name: str, last_name: str) -> str:
    base = f"{first_name.lower().split()[0]}.{last_name.lower().replace(' ', '-')}"
    base = "".join(c for c in base if c.isalnum() or c in ".-")
    username = base
    counter = 1
    while db.query(User).filter(User.username == username).first():
        username = f"{base}{counter}"
        counter += 1
    return username


def _get_user_or_404(db: Session, user_id):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise PolicyError("ACCOUNT", "Utilisateur introuvable.", 404)
    return user


def _get_admin_emails(db: Session) -> list[str]:
    admins = (
        db.query(User)
        .filter(
            User.role.in_([UserRoleEnum.ADMIN, UserRoleEnum.SUPER_ADMIN]),
            User.is_active == True,  # noqa: E712
        )
        .all()
    )
    return [a.email for a in admins]
