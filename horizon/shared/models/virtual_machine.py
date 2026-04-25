"""Machines virtuelles et réservations."""

import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as PgEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from horizon.shared.models.base import Base, TimestampMixin


class PhysicalNode(str, enum.Enum):
    REM = "REM"
    RAM = "RAM"
    EMILIA = "EMILIA"


class VMStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    STOPPED = "STOPPED"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"
    PENDING = "PENDING"


class VirtualMachine(Base, TimestampMixin):
    __tablename__ = "virtual_machines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proxmox_vmid = Column(Integer, nullable=False, unique=True, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)

    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    node = Column(PgEnum(PhysicalNode, name="physical_node_enum"), nullable=False)

    vcpu = Column(Integer, nullable=False)
    ram_gb = Column(Float, nullable=False)
    storage_gb = Column(Float, nullable=False)

    iso_image_id = Column(
        UUID(as_uuid=True), ForeignKey("iso_images.id", ondelete="SET NULL"), nullable=True
    )

    status = Column(
        PgEnum(VMStatus, name="vm_status_enum"), nullable=False, default=VMStatus.PENDING
    )
    lease_start = Column(DateTime(timezone=True), nullable=False)
    lease_end = Column(DateTime(timezone=True), nullable=False)
    stopped_at = Column(DateTime(timezone=True), nullable=True)

    vlan_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    ssh_public_key = Column(Text, nullable=True)
    shared_space_gb = Column(Float, nullable=False, default=0.0)

    owner = relationship("User", back_populates="virtual_machines", foreign_keys=[owner_id])
    iso_image = relationship("ISOImage", back_populates="virtual_machines")
    reservations = relationship(
        "Reservation", back_populates="vm", cascade="all, delete-orphan"
    )
    quota_violations = relationship("QuotaViolation", back_populates="vm")
    security_incidents = relationship("SecurityIncident", back_populates="vm")


class Reservation(Base, TimestampMixin):
    __tablename__ = "reservations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vm_id = Column(
        UUID(as_uuid=True), ForeignKey("virtual_machines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    extended = Column(Boolean, nullable=False, default=False)
    extension_of = Column(UUID(as_uuid=True), ForeignKey("reservations.id"), nullable=True)

    vm = relationship("VirtualMachine", back_populates="reservations")
    user = relationship("User", foreign_keys=[user_id])
    parent = relationship(
        "Reservation", remote_side="Reservation.id", foreign_keys=[extension_of]
    )
