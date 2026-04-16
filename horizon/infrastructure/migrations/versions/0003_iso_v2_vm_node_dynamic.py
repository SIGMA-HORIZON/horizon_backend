"""
Migration 0003 — ISO v2 + VirtualMachine.proxmox_node dynamique.

Changements :
1. Table iso_images :
   - Ajout source_url, status (enum iso_status_enum), created_by_id,
     proxmox_upid, proxmox_node, proxmox_storage, size_bytes, error_message
   - Ajout valeur "OTHER" dans os_family_enum (si absent)

2. Table virtual_machines :
   - Renommage colonne `node` (PhysicalNode enum) → `proxmox_node` (VARCHAR 64)
   - Ajout creation_mode (enum vm_creation_mode_enum)
   - Ajout template_vmid, last_upid, cloudinit_user
   - Suppression de l'ancien enum physical_node_enum (après migration des données)

Stratégie de migration sans downtime :
  - Ajout des nouvelles colonnes avec valeurs par défaut
  - Copie des données node → proxmox_node (valeur textuelle de l'enum)
  - Suppression de l'ancienne colonne node
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # ──────────────────────────────────────────────────────────────────────
    # 1. Nouveau type ENUM iso_status_enum
    # ──────────────────────────────────────────────────────────────────────
    iso_status_enum = postgresql.ENUM(
        "DOWNLOADING", "PENDING_ANALYST", "VALIDATED", "ERROR",
        name="iso_status_enum",
    )
    iso_status_enum.create(conn, checkfirst=True)

    # ──────────────────────────────────────────────────────────────────────
    # 2. Ajout valeur "OTHER" dans os_family_enum (PostgreSQL ALTER TYPE)
    # ──────────────────────────────────────────────────────────────────────
    result = conn.execute(
        sa.text("SELECT unnest(enum_range(NULL::os_family_enum))::text")
    ).fetchall()
    existing_vals = {r[0] for r in result}
    if "OTHER" not in existing_vals:
        conn.execute(sa.text("ALTER TYPE os_family_enum ADD VALUE IF NOT EXISTS 'OTHER'"))

    # ──────────────────────────────────────────────────────────────────────
    # 3. Nouvelles colonnes iso_images
    # ──────────────────────────────────────────────────────────────────────
    with op.batch_alter_table("iso_images") as batch:
        batch.add_column(
            sa.Column("source_url", sa.Text(), nullable=True)
        )
        batch.add_column(
            sa.Column(
                "status",
                sa.Enum(
                    "DOWNLOADING", "PENDING_ANALYST", "VALIDATED", "ERROR",
                    name="iso_status_enum",
                    create_constraint=False,
                ),
                nullable=False,
                server_default="PENDING_ANALYST",
            )
        )
        batch.add_column(
            sa.Column(
                "created_by_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            )
        )
        batch.add_column(sa.Column("proxmox_upid", sa.String(256), nullable=True))
        batch.add_column(sa.Column("proxmox_node", sa.String(64), nullable=True))
        batch.add_column(sa.Column("proxmox_storage", sa.String(64), nullable=True))
        batch.add_column(sa.Column("size_bytes", sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column("error_message", sa.Text(), nullable=True))

    # Index sur source_url pour le cache
    op.create_index("ix_iso_images_source_url", "iso_images", ["source_url"])

    # Rétrocompatibilité : les ISOs existantes (ajoutées manuellement) passent VALIDATED
    conn.execute(
        sa.text("UPDATE iso_images SET status = 'VALIDATED' WHERE is_active = true")
    )
    conn.execute(
        sa.text("UPDATE iso_images SET status = 'PENDING_ANALYST' WHERE is_active = false")
    )

    # ──────────────────────────────────────────────────────────────────────
    # 4. Nouveau type ENUM vm_creation_mode_enum
    # ──────────────────────────────────────────────────────────────────────
    vm_mode_enum = postgresql.ENUM(
        "TEMPLATE", "MANUAL",
        name="vm_creation_mode_enum",
    )
    vm_mode_enum.create(conn, checkfirst=True)

    # Ajout valeur ERROR dans vm_status_enum si absente
    result2 = conn.execute(
        sa.text("SELECT unnest(enum_range(NULL::vm_status_enum))::text")
    ).fetchall()
    existing_status = {r[0] for r in result2}
    if "ERROR" not in existing_status:
        conn.execute(sa.text("ALTER TYPE vm_status_enum ADD VALUE IF NOT EXISTS 'ERROR'"))

    # ──────────────────────────────────────────────────────────────────────
    # 5. Modifications virtual_machines
    # ──────────────────────────────────────────────────────────────────────
    # 5a. Ajout proxmox_node (VARCHAR) avec valeur par défaut temporaire
    op.add_column(
        "virtual_machines",
        sa.Column("proxmox_node", sa.String(64), nullable=True),
    )

    # 5b. Copier les valeurs de l'ancien Enum 'node' → proxmox_node
    conn.execute(
        sa.text("UPDATE virtual_machines SET proxmox_node = node::text WHERE node IS NOT NULL")
    )

    # 5c. Rendre proxmox_node NOT NULL avec valeur par défaut de secours
    conn.execute(
        sa.text("UPDATE virtual_machines SET proxmox_node = 'unknown' WHERE proxmox_node IS NULL")
    )
    op.alter_column("virtual_machines", "proxmox_node", nullable=False)

    # 5d. Nouvelles colonnes VMs
    with op.batch_alter_table("virtual_machines") as batch:
        batch.add_column(
            sa.Column(
                "creation_mode",
                sa.Enum("TEMPLATE", "MANUAL", name="vm_creation_mode_enum", create_constraint=False),
                nullable=False,
                server_default="MANUAL",
            )
        )
        batch.add_column(sa.Column("template_vmid", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("last_upid", sa.String(256), nullable=True))
        batch.add_column(sa.Column("cloudinit_user", sa.String(128), nullable=True))

    # 5e. Supprimer l'ancienne colonne 'node' (enum physical_node_enum)
    op.drop_column("virtual_machines", "node")

    # Note : physical_node_enum est conservé en base pour compatibilité
    # avec proxmox_node_mappings ; ne pas le supprimer ici.


def downgrade() -> None:
    conn = op.get_bind()

    # Recréer la colonne node
    physical_node_enum = postgresql.ENUM(
        "MAITRE","ESCLAVE", "REM", "RAM", "EMILIA",
        name="physical_node_enum",
    )
    physical_node_enum.create(conn, checkfirst=True)

    op.add_column(
        "virtual_machines",
        sa.Column(
            "node",
            sa.Enum("MAITRE","ESCLAVE", "REM", "RAM", "EMILIA", name="physical_node_enum", create_constraint=False),
            nullable=True,
        ),
    )
    conn.execute(
        sa.text("UPDATE virtual_machines SET node = 'REM' WHERE proxmox_node IS NOT NULL")
    )
    op.alter_column("virtual_machines", "node", nullable=False)

    with op.batch_alter_table("virtual_machines") as batch:
        batch.drop_column("cloudinit_user")
        batch.drop_column("last_upid")
        batch.drop_column("template_vmid")
        batch.drop_column("creation_mode")

    op.drop_column("virtual_machines", "proxmox_node")

    op.drop_index("ix_iso_images_source_url", table_name="iso_images")
    with op.batch_alter_table("iso_images") as batch:
        batch.drop_column("error_message")
        batch.drop_column("size_bytes")
        batch.drop_column("proxmox_storage")
        batch.drop_column("proxmox_node")
        batch.drop_column("proxmox_upid")
        batch.drop_column("created_by_id")
        batch.drop_column("status")
        batch.drop_column("source_url")

    conn.execute(sa.text("DROP TYPE IF EXISTS iso_status_enum"))
    conn.execute(sa.text("DROP TYPE IF EXISTS vm_creation_mode_enum"))
