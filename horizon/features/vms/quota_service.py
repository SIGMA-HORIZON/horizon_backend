"""Résolution des quotas effectifs."""

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from horizon.core.config import get_settings
from horizon.shared.models import QuotaOverride, QuotaPolicy, User, VirtualMachine, VMStatus

cfg = get_settings()


@dataclass
class EffectiveQuota:
    max_vcpu_per_vm: int
    max_ram_gb_per_vm: float
    max_storage_gb_per_vm: float
    max_shared_space_gb: float
    max_simultaneous_vms: int
    max_session_duration_hours: int


def get_effective_quota(db: Session, user_id) -> EffectiveQuota:
    user: Optional[User] = db.query(User).filter(User.id == user_id).first()

    base = EffectiveQuota(
        max_vcpu_per_vm=cfg.DEFAULT_MAX_VCPU_PER_VM,
        max_ram_gb_per_vm=cfg.DEFAULT_MAX_RAM_GB,
        max_storage_gb_per_vm=cfg.DEFAULT_MAX_STORAGE_GB,
        max_shared_space_gb=cfg.DEFAULT_MAX_SHARED_SPACE_GB,
        max_simultaneous_vms=cfg.DEFAULT_MAX_SIMULTANEOUS_VMS,
        max_session_duration_hours=cfg.DEFAULT_MAX_SESSION_HOURS,
    )

    if user and user.quota_policy_id:
        policy: Optional[QuotaPolicy] = (
            db.query(QuotaPolicy)
            .filter(
                QuotaPolicy.id == user.quota_policy_id,
                QuotaPolicy.is_active == True,  # noqa: E712
            )
            .first()
        )
        if policy:
            base = EffectiveQuota(
                max_vcpu_per_vm=policy.max_vcpu_per_vm,
                max_ram_gb_per_vm=policy.max_ram_gb_per_vm,
                max_storage_gb_per_vm=policy.max_storage_gb_per_vm,
                max_shared_space_gb=policy.max_shared_space_gb,
                max_simultaneous_vms=policy.max_simultaneous_vms,
                max_session_duration_hours=policy.max_session_duration_hours,
            )

    if user:
        override: Optional[QuotaOverride] = (
            db.query(QuotaOverride).filter(QuotaOverride.user_id == user_id).first()
        )
        if override:
            if override.max_vcpu_per_vm is not None:
                base.max_vcpu_per_vm = override.max_vcpu_per_vm
            if override.max_ram_gb_per_vm is not None:
                base.max_ram_gb_per_vm = override.max_ram_gb_per_vm
            if override.max_storage_gb_per_vm is not None:
                base.max_storage_gb_per_vm = override.max_storage_gb_per_vm
            if override.max_shared_space_gb is not None:
                base.max_shared_space_gb = override.max_shared_space_gb
            if override.max_simultaneous_vms is not None:
                base.max_simultaneous_vms = override.max_simultaneous_vms
            if override.max_session_duration_hours is not None:
                base.max_session_duration_hours = override.max_session_duration_hours

    return base


def count_active_vms(db: Session, user_id) -> int:
    return (
        db.query(VirtualMachine)
        .filter(
            VirtualMachine.owner_id == user_id,
            VirtualMachine.status.in_([VMStatus.ACTIVE, VMStatus.PENDING]),
        )
        .count()
    )
