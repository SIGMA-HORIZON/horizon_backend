"""Audit, tentatives de login, incidents, violations."""

import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum as PgEnum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from horizon.shared.models.base import Base


class AuditAction(str, enum.Enum):
    ACCOUNT_REQUEST_SUBMITTED = "ACCOUNT_REQUEST_SUBMITTED"
    ACCOUNT_APPROVED = "ACCOUNT_APPROVED"
    ACCOUNT_REJECTED = "ACCOUNT_REJECTED"
    ACCOUNT_SUSPENDED = "ACCOUNT_SUSPENDED"
    ACCOUNT_REACTIVATED = "ACCOUNT_REACTIVATED"
    ACCOUNT_DELETED = "ACCOUNT_DELETED"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    PASSWORD_RESET = "PASSWORD_RESET"
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGOUT = "LOGOUT"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    VM_CREATED = "VM_CREATED"
    VM_STARTED = "VM_STARTED"
    VM_STOPPED = "VM_STOPPED"
    VM_FORCE_STOPPED = "VM_FORCE_STOPPED"
    VM_DELETED = "VM_DELETED"
    VM_ADMIN_DELETED = "VM_ADMIN_DELETED"
    VM_MODIFIED = "VM_MODIFIED"
    VM_EXPIRED = "VM_EXPIRED"
    VM_LEASE_EXTENDED = "VM_LEASE_EXTENDED"
    QUOTA_POLICY_MODIFIED = "QUOTA_POLICY_MODIFIED"
    QUOTA_OVERRIDE_GRANTED = "QUOTA_OVERRIDE_GRANTED"
    ISO_IMAGE_ADDED = "ISO_IMAGE_ADDED"
    ISO_IMAGE_DISABLED = "ISO_IMAGE_DISABLED"
    FILE_DOWNLOADED = "FILE_DOWNLOADED"
    SECURITY_INCIDENT_CREATED = "SECURITY_INCIDENT_CREATED"
    SECURITY_INCIDENT_RESOLVED = "SECURITY_INCIDENT_RESOLVED"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action = Column(PgEnum(AuditAction, name="audit_action_enum"), nullable=False, index=True)
    target_type = Column(String(64), nullable=True)
    target_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    # Colonne SQL "metadata" - nom Python log_metadata (réservé sur DeclarativeBase)
    log_metadata = Column("metadata", JSONB, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    actor = relationship("User", back_populates="audit_logs", foreign_keys=[actor_id])


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    username_tried = Column(String(64), nullable=True)
    success = Column(Boolean, nullable=False)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    user = relationship("User", back_populates="login_attempts")


class IncidentType(str, enum.Enum):
    UNAUTHORIZED_VM_ACCESS = "UNAUTHORIZED_VM_ACCESS"
    UNAUTHORIZED_API_ACCESS = "UNAUTHORIZED_API_ACCESS"
    NETWORK_SCAN_DETECTED = "NETWORK_SCAN_DETECTED"
    EXPLOIT_TOOL_DETECTED = "EXPLOIT_TOOL_DETECTED"
    CRYPTO_MINING_DETECTED = "CRYPTO_MINING_DETECTED"
    SUSPICIOUS_TRAFFIC = "SUSPICIOUS_TRAFFIC"
    POLICY_VIOLATION = "POLICY_VIOLATION"


class IncidentSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"


class SecurityIncident(Base):
    __tablename__ = "security_incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vm_id = Column(
        UUID(as_uuid=True), ForeignKey("virtual_machines.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    incident_type = Column(PgEnum(IncidentType, name="incident_type_enum"), nullable=False)
    severity = Column(PgEnum(IncidentSeverity, name="incident_severity_enum"), nullable=False)
    status = Column(
        PgEnum(IncidentStatus, name="incident_status_enum"),
        nullable=False,
        default=IncidentStatus.OPEN,
    )
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    vm = relationship("VirtualMachine", back_populates="security_incidents")
    user = relationship("User", foreign_keys=[user_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])


class ViolationType(str, enum.Enum):
    CPU = "CPU"
    RAM = "RAM"
    STORAGE = "STORAGE"
    SESSION_TIME = "SESSION_TIME"
    SHARED_SPACE = "SHARED_SPACE"
    VM_COUNT = "VM_COUNT"


class SanctionLevel(str, enum.Enum):
    LEVEL_1 = "LEVEL_1"
    LEVEL_2 = "LEVEL_2"
    LEVEL_3 = "LEVEL_3"


class QuotaViolation(Base):
    __tablename__ = "quota_violations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vm_id = Column(
        UUID(as_uuid=True), ForeignKey("virtual_machines.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    violation_type = Column(PgEnum(ViolationType, name="violation_type_enum"), nullable=False)
    sanction_level = Column(
        PgEnum(SanctionLevel, name="sanction_level_enum"),
        nullable=False,
        default=SanctionLevel.LEVEL_1,
    )
    observed_value = Column(Float, nullable=False)
    limit_value = Column(Float, nullable=False)
    resolved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)

    vm = relationship("VirtualMachine", back_populates="quota_violations")
    user = relationship("User", foreign_keys=[user_id])
