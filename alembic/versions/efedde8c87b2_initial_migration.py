"""Initial migration - create all tables

Revision ID: efedde8c87b2
Revises: 
Create Date: 2026-03-29 12:18:42.620541

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'efedde8c87b2'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all core tables."""

    # --- roles ---
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_type', sa.Enum('user', 'admin', name='roletype'), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_type'),
    )

    # --- users ---
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('first_name', sa.String(length=128), nullable=False),
        sa.Column('last_name', sa.String(length=128), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('must_change_password', sa.Boolean(), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('suspended_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # --- usage_policies ---
    op.create_table(
        'usage_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('notice_minutes_before', sa.Integer(), nullable=False),
        sa.Column('max_inactive_days', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('notice_minutes_before > 0', name='chk_notice_minutes_before_positive'),
        sa.CheckConstraint('max_inactive_days > 0', name='chk_max_inactive_days_positive'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # --- quotas ---
    op.create_table(
        'quotas',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('max_cpu_cores', sa.Integer(), nullable=False),
        sa.Column('max_ram_gb', sa.Integer(), nullable=False),
        sa.Column('max_disk_gb', sa.Integer(), nullable=False),
        sa.Column('max_concurrent_vms', sa.Integer(), nullable=False),
        sa.Column('max_session_hours', sa.Integer(), nullable=False),
        sa.Column('max_shared_space_gb', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['policy_id'], ['usage_policies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('policy_id'),
    )

    # --- physical_nodes ---
    op.create_table(
        'physical_nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hostname', sa.String(length=64), nullable=False),
        sa.Column('status', sa.Enum('online', 'offline', 'maintenance', name='nodestatus'), nullable=False),
        sa.Column('total_cpu_cores', sa.Integer(), nullable=False),
        sa.Column('total_ram_gb', sa.Integer(), nullable=False),
        sa.Column('total_disk_gb', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hostname'),
    )

    # --- iso_images ---
    op.create_table(
        'iso_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('os_type', sa.Enum('linux', 'windows', name='ostype'), nullable=False),
        sa.Column('version', sa.String(length=64), nullable=False),
        sa.Column('proxmox_ref', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('proxmox_ref'),
    )

    # --- ssh_keys ---
    op.create_table(
        'ssh_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('public_key', sa.Text(), nullable=False),
        sa.Column('algorithm', sa.Enum('ed25519', 'rsa4096', name='sshalgorithm'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('downloaded_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- virtual_machines ---
    op.create_table(
        'virtual_machines',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('iso_image_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ssh_key_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('status', sa.Enum('provisioning', 'active', 'stopped', 'expired', 'deleted', name='vmstatus'), nullable=False),
        sa.Column('cpu_cores', sa.Integer(), nullable=False),
        sa.Column('ram_gb', sa.Integer(), nullable=False),
        sa.Column('disk_gb', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_hours', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['policy_id'], ['usage_policies.id']),
        sa.ForeignKeyConstraint(['node_id'], ['physical_nodes.id']),
        sa.ForeignKeyConstraint(['iso_image_id'], ['iso_images.id']),
        sa.ForeignKeyConstraint(['ssh_key_id'], ['ssh_keys.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ssh_key_id'),
    )

    # --- audit_logs ---
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action_type', sa.Enum(
            'login', 'logout', 'login_failed',
            'vm_create', 'vm_stop', 'vm_delete', 'vm_modify', 'vm_extend',
            'ssh_connect',
            'admin_account_create', 'admin_account_modify', 'admin_account_suspend',
            'admin_vm_force_stop', 'admin_policy_modify', 'policy_violation',
            name='actiontype'
        ), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- notifications ---
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('notif_type', sa.Enum(
            'expiry_warning', 'vm_stopped', 'vm_deleted', 'account_suspended',
            name='notiftype'
        ), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- account_requests ---
    op.create_table(
        'account_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=128), nullable=False),
        sa.Column('last_name', sa.String(length=128), nullable=False),
        sa.Column('organisation', sa.String(length=255), nullable=True),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='accountrequeststatus'), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['processed_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_account_requests_email'), 'account_requests', ['email'], unique=False)


def downgrade() -> None:
    """Drop all tables and types."""
    op.drop_index(op.f('ix_account_requests_email'), table_name='account_requests')
    op.drop_table('account_requests')
    op.drop_table('notifications')
    op.drop_table('audit_logs')
    op.drop_table('virtual_machines')
    op.drop_table('ssh_keys')
    op.drop_table('iso_images')
    op.drop_table('physical_nodes')
    op.drop_table('quotas')
    op.drop_table('usage_policies')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('roles')
    op.execute('DROP TYPE IF EXISTS accountrequeststatus')
    op.execute('DROP TYPE IF EXISTS notiftype')
    op.execute('DROP TYPE IF EXISTS actiontype')
    op.execute('DROP TYPE IF EXISTS sshalgorithm')
    op.execute('DROP TYPE IF EXISTS ostype')
    op.execute('DROP TYPE IF EXISTS nodestatus')
    op.execute('DROP TYPE IF EXISTS vmstatus')
    op.execute('DROP TYPE IF EXISTS roletype')
