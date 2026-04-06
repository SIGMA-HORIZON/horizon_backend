"""Enforcement POL-SIGMA-HORIZON-v1.0."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status

from horizon.core.config import get_settings
from horizon.core.constants import CHANGE_PASSWORD_PATH

settings = get_settings()


class PolicyError(HTTPException):
    def __init__(self, policy_id: str, detail: str, status_code: int = status.HTTP_403_FORBIDDEN):
        super().__init__(status_code=status_code, detail=f"[{policy_id}] {detail}")


def enforce_password_strength(password: str) -> None:
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        raise PolicyError(
            "POL-COMPTE-02",
            f"Le mot de passe doit contenir au moins {settings.PASSWORD_MIN_LENGTH} caractères.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    checks = [
        any(c.isupper() for c in password),
        any(c.islower() for c in password),
        any(c.isdigit() for c in password),
        any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password),
    ]
    if not all(checks):
        raise PolicyError(
            "POL-COMPTE-02",
            "Le mot de passe doit contenir au moins une majuscule, une minuscule, un chiffre et un caractère spécial.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


def enforce_account_not_locked(locked_until: Optional[datetime]) -> None:
    if locked_until and datetime.now(timezone.utc) < locked_until:
        remaining = int((locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
        raise PolicyError(
            "POL-COMPTE-02",
            f"Compte temporairement verrouillé. Réessayez dans {remaining} minute(s).",
            status.HTTP_429_TOO_MANY_REQUESTS,
        )


def enforce_account_active(is_active: bool) -> None:
    if not is_active:
        raise PolicyError(
            "POL-COMPTE-03",
            "Ce compte est suspendu. Contactez un administrateur.",
            status.HTTP_403_FORBIDDEN,
        )


def enforce_must_change_password(must_change_pwd: bool, path: str) -> None:
    if must_change_pwd and path != CHANGE_PASSWORD_PATH:
        raise PolicyError(
            "POL-COMPTE-02",
            "Vous devez changer votre mot de passe provisoire avant d'accéder à la plateforme.",
            status.HTTP_403_FORBIDDEN,
        )


def enforce_vm_resource_limits(
    vcpu: int,
    ram_gb: float,
    storage_gb: float,
    max_vcpu: int,
    max_ram_gb: float,
    max_storage_gb: float,
) -> None:
    errors = []
    if vcpu > max_vcpu:
        errors.append(f"CPU : demandé {vcpu} vCores, maximum autorisé {max_vcpu}")
    if ram_gb > max_ram_gb:
        errors.append(f"RAM : demandé {ram_gb} Go, maximum autorisé {max_ram_gb}")
    if storage_gb > max_storage_gb:
        errors.append(f"Stockage : demandé {storage_gb} Go, maximum autorisé {max_storage_gb}")
    if errors:
        raise PolicyError(
            "POL-RESSOURCES",
            "Ressources demandées dépassent vos quotas : " + " | ".join(errors),
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


def enforce_vm_count_limit(current_vm_count: int, max_simultaneous_vms: int) -> None:
    if current_vm_count >= max_simultaneous_vms:
        raise PolicyError(
            "POL-RESSOURCES",
            f"Vous avez atteint le nombre maximum de VM simultanées ({max_simultaneous_vms}).",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


def enforce_session_duration(requested_hours: int, max_hours: int) -> None:
    if requested_hours <= 0:
        raise PolicyError(
            "POL-RESSOURCES-01",
            "La durée de session doit être supérieure à 0.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    if requested_hours > max_hours:
        raise PolicyError(
            "POL-RESSOURCES-01",
            f"Durée demandée ({requested_hours}h) dépasse le maximum autorisé ({max_hours}h).",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


def enforce_hard_limits(vcpu: int, ram_gb: float, storage_gb: float, session_hours: int) -> None:
    if vcpu > settings.HARD_LIMIT_VCPU:
        raise PolicyError(
            "POL-RESSOURCES", f"CPU dépasse le plafond absolu ({settings.HARD_LIMIT_VCPU} vCores)."
        )
    if ram_gb > settings.HARD_LIMIT_RAM_GB:
        raise PolicyError(
            "POL-RESSOURCES", f"RAM dépasse le plafond absolu ({settings.HARD_LIMIT_RAM_GB} Go)."
        )
    if storage_gb > settings.HARD_LIMIT_STORAGE_GB:
        raise PolicyError(
            "POL-RESSOURCES",
            f"Stockage dépasse le plafond absolu ({settings.HARD_LIMIT_STORAGE_GB} Go).",
        )
    if session_hours > settings.HARD_LIMIT_SESSION_HOURS:
        raise PolicyError(
            "POL-RESSOURCES-01",
            f"Durée dépasse le plafond absolu ({settings.HARD_LIMIT_SESSION_HOURS}h).",
        )


def enforce_iso_authorized(iso_is_active: bool) -> None:
    if not iso_is_active:
        raise PolicyError(
            "POL-RESSOURCES-02",
            "Cette image ISO n'est pas autorisée ou a été désactivée par l'administrateur.",
        )


def enforce_vm_ownership(vm_owner_id, current_user_id, user_role: str) -> None:
    if str(vm_owner_id) != str(current_user_id) and user_role not in ("ADMIN", "SUPER_ADMIN"):
        raise PolicyError(
            "BD-02",
            "Vous n'êtes pas autorisé à effectuer cette action sur cette VM.",
        )


def enforce_vm_not_expired(lease_end: datetime) -> None:
    if datetime.now(timezone.utc) > lease_end:
        raise PolicyError(
            "POL-RESSOURCES-01",
            "Cette VM a expiré. Créez une nouvelle VM ou prolongez votre session.",
        )


def enforce_role(user_role: str, required_roles: list[str]) -> None:
    if user_role not in required_roles:
        raise PolicyError(
            "POL-SEC-01",
            f"Action réservée aux rôles : {', '.join(required_roles)}.",
            status.HTTP_403_FORBIDDEN,
        )


def enforce_admin_action_logged(actor_id) -> None:
    if not actor_id:
        raise PolicyError(
            "POL-SEC-03",
            "Action administrative non tracée. actor_id manquant.",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def enforce_shared_space_available(vm_stopped_at: Optional[datetime]) -> None:
    if vm_stopped_at:
        deadline = vm_stopped_at + timedelta(hours=settings.SHARED_SPACE_RETENTION_HOURS)
        if datetime.now(timezone.utc) > deadline:
            raise PolicyError(
                "POL-FICHIERS-01",
                "L'espace partagé de cette VM a été purgé (délai de 24h dépassé après extinction).",
                status.HTTP_410_GONE,
            )
