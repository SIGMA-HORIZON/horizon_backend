"""Utilisateur."""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum as PgEnum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from horizon.shared.models.base import Base, TimestampMixin
from horizon.shared.models.role import UserRoleEnum


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(64), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    organisation = Column(String(255), nullable=True)

    role = Column(
        PgEnum(UserRoleEnum, name="user_role_enum"),
        nullable=False,
        default=UserRoleEnum.USER,
    )
    role_id = Column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="SET NULL"), nullable=True
    )

    must_change_pwd = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    failed_login_count = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    quota_policy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("quota_policies.id", ondelete="SET NULL"),
        nullable=True,
    )

    role_obj = relationship("Role", back_populates="users", foreign_keys=[role_id])
    quota_policy = relationship(
        "QuotaPolicy", back_populates="users", foreign_keys=[quota_policy_id]
    )
    quota_override = relationship(
        "QuotaOverride",
        back_populates="user",
        foreign_keys="QuotaOverride.user_id",
        uselist=False,
    )
    virtual_machines = relationship(
        "VirtualMachine",
        back_populates="owner",
        foreign_keys="VirtualMachine.owner_id",
    )
    audit_logs = relationship(
        "AuditLog", back_populates="actor", foreign_keys="AuditLog.actor_id"
    )
    login_attempts = relationship("LoginAttempt", back_populates="user")
    account_request = relationship(
        "AccountRequest",
        back_populates="user",
        uselist=False,
        foreign_keys="AccountRequest.user_id",
    )
