"""Correspondances ISO ↔ template Proxmox et nœud métier ↔ nœud Proxmox."""

import uuid

from sqlalchemy import Column, Enum as PgEnum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from horizon.shared.models.virtual_machine import PhysicalNode
from sqlalchemy.orm import relationship

from horizon.shared.models.base import Base, TimestampMixin


class IsoProxmoxTemplate(Base, TimestampMixin):
    __tablename__ = "iso_proxmox_templates"
    __table_args__ = (UniqueConstraint(
        "iso_image_id", name="uq_iso_proxmox_template_iso"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iso_image_id = Column(
        UUID(as_uuid=True),
        ForeignKey("iso_images.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    proxmox_template_vmid = Column(Integer, nullable=False)

    iso_image = relationship("ISOImage", back_populates="proxmox_template_map")


class ProxmoxNodeMapping(Base, TimestampMixin):
    __tablename__ = "proxmox_node_mappings"
    __table_args__ = (UniqueConstraint(
        "physical_node", name="uq_proxmox_node_mapping_node"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    physical_node = Column(
            PgEnum(PhysicalNode, name="physical_node_enum", create_constraint=False),
            nullable=False,
            unique=True,
        )
    proxmox_node_name = Column(String(64), nullable=False)
