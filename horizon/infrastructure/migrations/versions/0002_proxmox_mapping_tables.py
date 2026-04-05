"""Tables correspondance Proxmox (ISO-template, nœuds)

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-04
"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

_physical_node = postgresql.ENUM(
    "REM", "RAM", "EMILIA", name="physical_node_enum", create_type=False
)


def upgrade() -> None:
    op.create_table(
        "iso_proxmox_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("iso_image_id", postgresql.UUID(
            as_uuid=True), nullable=False),
        sa.Column("proxmox_template_vmid", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["iso_image_id"], ["iso_images.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "iso_image_id", name="uq_iso_proxmox_template_iso"),
    )

    op.create_table(
        "proxmox_node_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("physical_node", _physical_node, nullable=False),
        sa.Column("proxmox_node_name", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "physical_node", name="uq_proxmox_node_mapping_node"),
    )

    conn = op.get_bind()
    for pn, name in [("REM", "pve-rem"), ("RAM", "pve-ram"), ("EMILIA", "pve-emilia")]:
        conn.execute(
            sa.text(
                "INSERT INTO proxmox_node_mappings (id, physical_node, proxmox_node_name) "
                "VALUES (:id, CAST(:pn AS physical_node_enum), :name)"
            ),
            {"id": uuid.uuid4(), "pn": pn, "name": name},
        )


def downgrade() -> None:
    op.drop_table("proxmox_node_mappings")
    op.drop_table("iso_proxmox_templates")
