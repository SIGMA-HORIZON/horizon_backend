from typing import List, Optional
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, Integer, Enum, DateTime, Text, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, INET

from app.db.base import Base
from app.models.enums import RoleType, VMStatus, NodeStatus, OSType, SSHAlgorithm, ActionType, NotifType, AccountRequestStatus

class AccountRequest(Base):
    __tablename__ = "account_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    organisation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[AccountRequestStatus] = mapped_column(Enum(AccountRequestStatus, values_callable=lambda x: [e.value for e in x]), default=AccountRequestStatus.PENDING, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_type: Mapped[RoleType] = mapped_column(Enum(RoleType, values_callable=lambda x: [e.value for e in x]), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    users: Mapped[List["User"]] = relationship(back_populates="role")

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    suspended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    role: Mapped["Role"] = relationship(back_populates="users")
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="user")
    virtual_machines: Mapped[List["VirtualMachine"]] = relationship(back_populates="user")
    notifications: Mapped[List["Notification"]] = relationship(back_populates="user")

class UsagePolicy(Base):
    __tablename__ = "usage_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notice_minutes_before: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    max_inactive_days: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("notice_minutes_before > 0", name="chk_notice_minutes_before_positive"),
        CheckConstraint("max_inactive_days > 0", name="chk_max_inactive_days_positive"),
    )

    quota: Mapped["Quota"] = relationship(back_populates="policy", cascade="all, delete-orphan")
    virtual_machines: Mapped[List["VirtualMachine"]] = relationship(back_populates="policy")

class Quota(Base):
    __tablename__ = "quotas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usage_policies.id", ondelete="CASCADE"), nullable=False, unique=True)
    max_cpu_cores: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    max_ram_gb: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    max_disk_gb: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    max_concurrent_vms: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    max_session_hours: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    max_shared_space_gb: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    policy: Mapped["UsagePolicy"] = relationship(back_populates="quota")

class PhysicalNode(Base):
    __tablename__ = "physical_nodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hostname: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    status: Mapped[NodeStatus] = mapped_column(Enum(NodeStatus, values_callable=lambda x: [e.value for e in x]), default=NodeStatus.ONLINE, nullable=False)
    total_cpu_cores: Mapped[int] = mapped_column(Integer, nullable=False)
    total_ram_gb: Mapped[int] = mapped_column(Integer, nullable=False)
    total_disk_gb: Mapped[int] = mapped_column(Integer, nullable=False)

    virtual_machines: Mapped[List["VirtualMachine"]] = relationship(back_populates="node")

class ISOImage(Base):
    __tablename__ = "iso_images"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    os_type: Mapped[OSType] = mapped_column(Enum(OSType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    proxmox_ref: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    virtual_machines: Mapped[List["VirtualMachine"]] = relationship(back_populates="iso_image")

class SSHKey(Base):
    __tablename__ = "ssh_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    algorithm: Mapped[SSHAlgorithm] = mapped_column(Enum(SSHAlgorithm, values_callable=lambda x: [e.value for e in x]), default=SSHAlgorithm.ED25519, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    downloaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    virtual_machine: Mapped["VirtualMachine"] = relationship(back_populates="ssh_key")

class VirtualMachine(Base):
    __tablename__ = "virtual_machines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    policy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usage_policies.id"), nullable=False)
    node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("physical_nodes.id"), nullable=False)
    iso_image_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("iso_images.id"), nullable=False)
    ssh_key_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ssh_keys.id"), unique=True, nullable=False)
    
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[VMStatus] = mapped_column(Enum(VMStatus, values_callable=lambda x: [e.value for e in x]), default=VMStatus.PROVISIONING, nullable=False)
    cpu_cores: Mapped[int] = mapped_column(Integer, nullable=False)
    ram_gb: Mapped[int] = mapped_column(Integer, nullable=False)
    disk_gb: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="virtual_machines")
    policy: Mapped["UsagePolicy"] = relationship(back_populates="virtual_machines")
    node: Mapped["PhysicalNode"] = relationship(back_populates="virtual_machines")
    iso_image: Mapped["ISOImage"] = relationship(back_populates="virtual_machines")
    ssh_key: Mapped["SSHKey"] = relationship(back_populates="virtual_machine")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_type: Mapped[ActionType] = mapped_column(Enum(ActionType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[Optional["User"]] = relationship(back_populates="audit_logs")

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notif_type: Mapped[NotifType] = mapped_column(Enum(NotifType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="notifications")
