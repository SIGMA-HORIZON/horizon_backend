"""ISO et demandes de compte."""

import enum
import uuid

from sqlalchemy import Boolean, Column, Enum as PgEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from horizon.shared.models.base import Base, TimestampMixin


class OSFamily(str, enum.Enum):
    LINUX = "LINUX"
    WINDOWS = "WINDOWS"


class ISOImage(Base, TimestampMixin):
    __tablename__ = "iso_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), nullable=False, unique=True)
    filename = Column(String(255), nullable=False, unique=True)
    os_family = Column(PgEnum(OSFamily, name="os_family_enum"), nullable=False)
    os_version = Column(String(64), nullable=False)
    description = Column(String(512), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    added_by_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    added_by = relationship("User", foreign_keys=[added_by_id])
    virtual_machines = relationship(
        "VirtualMachine", back_populates="iso_image")
    proxmox_template_map = relationship(
        "IsoProxmoxTemplate",
        back_populates="iso_image",
        uselist=False,
        cascade="all, delete-orphan",
    )


class AccountRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AccountRequest(Base, TimestampMixin):
    __tablename__ = "account_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    organisation = Column(String(255), nullable=False)
    justification = Column(Text, nullable=True)

    status = Column(
        PgEnum(AccountRequestStatus, name="account_request_status_enum"),
        nullable=False,
        default=AccountRequestStatus.PENDING,
    )

    reviewed_by_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at = Column(String(64), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    user = relationship("User", foreign_keys=[
                        user_id], back_populates="account_request")
