"""Authentification — JWT, bcrypt, lockout."""

import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from horizon.core.config import get_settings
from horizon.infrastructure.email_service import send_login_alert_to_admin
from horizon.shared.audit_service import log_action
from horizon.shared.models import AuditAction, LoginAttempt, User, UserRoleEnum
from horizon.shared.policies.enforcer import (
    PolicyError,
    enforce_account_active,
    enforce_account_not_locked,
    enforce_password_strength,
)

settings = get_settings()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS,
)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def generate_temp_password(length: int | None = None) -> str:
    length = length or settings.TEMP_PASSWORD_LENGTH
    alphabet = string.ascii_letters + string.digits + "!@#$%&*-_"
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.isupper() for c in pwd)
            and any(c.islower() for c in pwd)
            and any(c.isdigit() for c in pwd)
            and any(c in "!@#$%&*-_" for c in pwd)
        ):
            return pwd


def create_access_token(user_id: str, role: str, must_change_pwd: bool = False) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "role": role,
        "must_change_pwd": must_change_pwd,
        "scope": "PASSWORD_CHANGE_ONLY" if must_change_pwd else "FULL_ACCESS",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as e:
        raise PolicyError("POL-SEC-02", f"Token invalide ou expiré : {e}", 401)


def authenticate_user(db: Session, username: str, password: str, ip_address: str) -> User:
    GENERIC_ERROR = PolicyError(
        "POL-COMPTE-02",
        "Identifiants incorrects.",
        401,
    )

    user: Optional[User] = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()

    attempt = LoginAttempt(
        id=uuid.uuid4(),
        user_id=user.id if user else None,
        username_tried=username,
        success=False,
        ip_address=ip_address,
        timestamp=datetime.now(timezone.utc),
    )

    if not user:
        db.add(attempt)
        db.commit()
        raise GENERIC_ERROR

    enforce_account_active(user.is_active)
    enforce_account_not_locked(user.locked_until)

    if not verify_password(password, user.hashed_password):
        user.failed_login_count += 1
        db.add(attempt)

        if user.failed_login_count >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=settings.LOGIN_LOCKOUT_MINUTES
            )
            log_action(
                db,
                None,
                AuditAction.ACCOUNT_LOCKED,
                "user",
                user.id,
                ip_address,
                {"failed_count": user.failed_login_count},
            )

        if user.failed_login_count == settings.ADMIN_ALERT_ATTEMPTS:
            admin_emails = _get_admin_emails(db)
            send_login_alert_to_admin(admin_emails, username, ip_address)

        db.commit()
        raise GENERIC_ERROR

    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    attempt.success = True
    db.add(attempt)

    log_action(db, user.id, AuditAction.LOGIN_SUCCESS, "user", user.id, ip_address)
    db.commit()

    return user


def change_password(db: Session, user_id: str, current_password: str, new_password: str) -> None:
    enforce_password_strength(new_password)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise PolicyError("AUTH", "Utilisateur introuvable.", 404)

    if not verify_password(current_password, user.hashed_password):
        raise PolicyError("POL-COMPTE-02", "Mot de passe actuel incorrect.", 401)

    user.hashed_password = hash_password(new_password)
    user.must_change_pwd = False
    log_action(db, user.id, AuditAction.PASSWORD_CHANGED, "user", user.id)
    db.commit()


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
