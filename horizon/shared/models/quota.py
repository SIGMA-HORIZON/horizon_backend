"""Politiques et overrides de quotas."""

import uuid

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from horizon.shared.models.base import Base, TimestampMixin


class QuotaPolicy(Base, TimestampMixin):
    __tablename__ = "quota_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(64), nullable=False, unique=True)
    description = Column(String(255), nullable=True)

    max_vcpu_per_vm = Column(Integer, nullable=False, default=2)
    max_ram_gb_per_vm = Column(Float, nullable=False, default=2.0)
    max_storage_gb_per_vm = Column(Float, nullable=False, default=20.0)
    max_shared_space_gb = Column(Float, nullable=False, default=5.0)
    max_simultaneous_vms = Column(Integer, nullable=False, default=2)
    max_session_duration_hours = Column(Integer, nullable=False, default=8)

    hard_limit_vcpu = Column(Integer, nullable=False, default=8)
    hard_limit_ram_gb = Column(Float, nullable=False, default=16.0)
    hard_limit_storage_gb = Column(Float, nullable=False, default=100.0)
    hard_limit_simultaneous_vms = Column(Integer, nullable=False, default=5)
    hard_limit_session_hours = Column(Integer, nullable=False, default=72)
    hard_limit_shared_space_gb = Column(Float, nullable=False, default=20.0)

    is_active = Column(Boolean, nullable=False, default=True)

    users = relationship("User", back_populates="quota_policy")


class QuotaOverride(Base, TimestampMixin):
    __tablename__ = "quota_overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    max_vcpu_per_vm = Column(Integer, nullable=True)
    max_ram_gb_per_vm = Column(Float, nullable=True)
    max_storage_gb_per_vm = Column(Float, nullable=True)
    max_shared_space_gb = Column(Float, nullable=True)
    max_simultaneous_vms = Column(Integer, nullable=True)
    max_session_duration_hours = Column(Integer, nullable=True)

    granted_by_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reason = Column(String(512), nullable=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="quota_override")
    granted_by = relationship("User", foreign_keys=[granted_by_id])
