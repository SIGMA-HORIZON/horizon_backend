"""Dépendances FastAPI — auth et rôles."""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from horizon.core.config import get_settings
from horizon.features.auth.service import decode_access_token
from horizon.infrastructure.database import get_db
from horizon.shared.models import User
from horizon.shared.policies.enforcer import (
    PolicyError,
    enforce_account_active,
    enforce_must_change_password,
    enforce_role,
)

settings = get_settings()
bearer_scheme = HTTPBearer()


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Session = Depends(get_db),
):
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise PolicyError("AUTH", "Token invalide : sub manquant.", 401)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise PolicyError("AUTH", "Utilisateur introuvable.", 401)

    enforce_account_active(user.is_active)
    enforce_must_change_password(user.must_change_pwd, request.url.path)

    return user


def require_role(*roles: str):
    def _check(user=Depends(get_current_user)):
        enforce_role(user.role.value, list(roles))
        return user

    return _check


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_role("ADMIN", "SUPER_ADMIN"))]
SuperAdmin = Annotated[User, Depends(require_role("SUPER_ADMIN"))]
