"""Initial schema - all Horizon tables

Revision ID: 0001
Revises: 
Create Date: 2025-03-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ ENUMS
    op.execute("CREATE TYPE user_role_enum AS ENUM ('USER','ADMIN','SUPER_ADMIN')")
    op.execute("CREATE TYPE os_family_enum AS ENUM ('LINUX','WINDOWS')")
    op.execute(
        "CREATE TYPE account_request_status_enum AS ENUM ('PENDING','APPROVED','REJECTED')")
    op.execute("CREATE TYPE physical_node_enum AS ENUM ('REM','RAM','EMILIA')")
    op.execute(
        "CREATE TYPE vm_status_enum AS ENUM ('ACTIVE','STOPPED','EXPIRED','SUSPENDED','PENDING')")
    op.execute("""CREATE TYPE audit_action_enum AS ENUM (
        'ACCOUNT_REQUEST_SUBMITTED','ACCOUNT_APPROVED','ACCOUNT_REJECTED',
        'ACCOUNT_SUSPENDED','ACCOUNT_REACTIVATED','ACCOUNT_DELETED',
        'PASSWORD_CHANGED','PASSWORD_RESET',
        'LOGIN_SUCCESS','LOGIN_FAILURE','LOGOUT','ACCOUNT_LOCKED',
        'VM_CREATED','VM_STARTED','VM_STOPPED','VM_FORCE_STOPPED',
        'VM_DELETED','VM_ADMIN_DELETED','VM_MODIFIED','VM_EXPIRED','VM_LEASE_EXTENDED',
        'QUOTA_POLICY_MODIFIED','QUOTA_OVERRIDE_GRANTED',
        'ISO_IMAGE_ADDED','ISO_IMAGE_DISABLED','FILE_DOWNLOADED',
        'SECURITY_INCIDENT_CREATED','SECURITY_INCIDENT_RESOLVED'
    )""")
    op.execute("CREATE TYPE incident_type_enum AS ENUM ('UNAUTHORIZED_VM_ACCESS','UNAUTHORIZED_API_ACCESS','NETWORK_SCAN_DETECTED','EXPLOIT_TOOL_DETECTED','CRYPTO_MINING_DETECTED','SUSPICIOUS_TRAFFIC','POLICY_VIOLATION')")
    op.execute(
        "CREATE TYPE incident_severity_enum AS ENUM ('LOW','MEDIUM','HIGH','CRITICAL')")
    op.execute(
        "CREATE TYPE incident_status_enum AS ENUM ('OPEN','INVESTIGATING','RESOLVED')")
    op.execute(
        "CREATE TYPE violation_type_enum AS ENUM ('CPU','RAM','STORAGE','SESSION_TIME','SHARED_SPACE','VM_COUNT')")
    op.execute(
        "CREATE TYPE sanction_level_enum AS ENUM ('LEVEL_1','LEVEL_2','LEVEL_3')")

    # --------------------------------------------------------------- roles
    op.create_table("roles",
                    sa.Column("id",          postgresql.UUID(
                        as_uuid=True), primary_key=True),
                    sa.Column("name",        sa.String(64),
                              nullable=False, unique=True),
                    sa.Column("description", sa.String(255), nullable=True),
                    sa.Column("created_at",  sa.DateTime(timezone=True),
                              server_default=sa.func.now(), nullable=False),
                    sa.Column("updated_at",  sa.DateTime(timezone=True),
                              server_default=sa.func.now(), nullable=False),
                    )

    op.create_table("role_permissions",
                    sa.Column("id",         postgresql.UUID(
                        as_uuid=True), primary_key=True),
                    sa.Column("role_id",    postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
                    sa.Column("permission", sa.String(128), nullable=False),
                    sa.UniqueConstraint("role_id", "permission",
                                        name="uq_role_permission"),
                    )

    # ---------------------------------------------------------- quota_policies
    op.create_table("quota_policies",
                    sa.Column("id",                          postgresql.UUID(
                        as_uuid=True), primary_key=True),
                    sa.Column("name",                        sa.String(
                        64),  nullable=False, unique=True),
                    sa.Column("description",
                              sa.String(255), nullable=True),
                    sa.Column("max_vcpu_per_vm",             sa.Integer(),
                              nullable=False, server_default="2"),
                    sa.Column("max_ram_gb_per_vm",           sa.Float(),
                              nullable=False, server_default="2.0"),
                    sa.Column("max_storage_gb_per_vm",       sa.Float(),
                              nullable=False, server_default="20.0"),
                    sa.Column("max_shared_space_gb",         sa.Float(),
                              nullable=False, server_default="5.0"),
                    sa.Column("max_simultaneous_vms",        sa.Integer(),
                              nullable=False, server_default="2"),
                    sa.Column("max_session_duration_hours",  sa.Integer(),
                              nullable=False, server_default="8"),
                    sa.Column("hard_limit_vcpu",             sa.Integer(),
                              nullable=False, server_default="8"),
                    sa.Column("hard_limit_ram_gb",           sa.Float(),
                              nullable=False, server_default="16.0"),
                    sa.Column("hard_limit_storage_gb",       sa.Float(),
                              nullable=False, server_default="100.0"),
                    sa.Column("hard_limit_simultaneous_vms", sa.Integer(),
                              nullable=False, server_default="5"),
                    sa.Column("hard_limit_session_hours",    sa.Integer(),
                              nullable=False, server_default="72"),
                    sa.Column("hard_limit_shared_space_gb",  sa.Float(),
                              nullable=False, server_default="20.0"),
                    sa.Column("is_active",                   sa.Boolean(),
                              nullable=False, server_default="true"),
                    sa.Column("created_at", sa.DateTime(timezone=True),
                              server_default=sa.func.now(), nullable=False),
                    sa.Column("updated_at", sa.DateTime(timezone=True),
                              server_default=sa.func.now(), nullable=False),
                    )

    # ----------------------------------------------------------------- users
    op.create_table("users",
                    sa.Column("id",                  postgresql.UUID(
                        as_uuid=True), primary_key=True),
                    sa.Column("username",            sa.String(
                        64),  nullable=False, unique=True),
                    sa.Column("email",               sa.String(
                        255), nullable=False, unique=True),
                    sa.Column("hashed_password",
                              sa.String(255), nullable=False),
                    sa.Column("first_name",          sa.String(
                        128), nullable=False),
                    sa.Column("last_name",           sa.String(
                        128), nullable=False),
                    sa.Column("organisation",
                              sa.String(255), nullable=True),
                    sa.Column("role",                postgresql.ENUM(
                        "USER", "ADMIN", "SUPER_ADMIN",
                        name="user_role_enum", create_type=False),
                        nullable=False, server_default="USER"),
                    sa.Column("role_id",             postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("roles.id", ondelete="SET NULL"), nullable=True),
                    sa.Column("must_change_pwd",     sa.Boolean(),
                              nullable=False, server_default="true"),
                    sa.Column("is_active",           sa.Boolean(),
                              nullable=False, server_default="true"),
                    sa.Column("failed_login_count",  sa.Integer(),
                              nullable=False, server_default="0"),
                    sa.Column("locked_until",        sa.DateTime(
                        timezone=True), nullable=True),
                    sa.Column("last_login_at",       sa.DateTime(
                        timezone=True), nullable=True),
                    sa.Column("quota_policy_id",     postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("quota_policies.id", ondelete="SET NULL"), nullable=True),
                    sa.Column("created_at", sa.DateTime(timezone=True),
                              server_default=sa.func.now(), nullable=False),
                    sa.Column("updated_at", sa.DateTime(timezone=True),
                              server_default=sa.func.now(), nullable=False),
                    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email",    "users", ["email"])

    # --------------------------------------------------------- quota_overrides
    op.create_table("quota_overrides",
                    sa.Column("id",                         postgresql.UUID(
                        as_uuid=True), primary_key=True),
                    sa.Column("user_id",                    postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
                    sa.Column("max_vcpu_per_vm",
                              sa.Integer(), nullable=True),
                    sa.Column("max_ram_gb_per_vm",
                              sa.Float(),   nullable=True),
                    sa.Column("max_storage_gb_per_vm",
                              sa.Float(),   nullable=True),
                    sa.Column("max_shared_space_gb",
                              sa.Float(),   nullable=True),
                    sa.Column("max_simultaneous_vms",
                              sa.Integer(), nullable=True),
                    sa.Column("max_session_duration_hours",
                              sa.Integer(), nullable=True),
                    sa.Column("granted_by_id",              postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
                    sa.Column("reason",    sa.String(512), nullable=True),
                    sa.Column("created_at", sa.DateTime(timezone=True),
                              server_default=sa.func.now(), nullable=False),
                    sa.Column("updated_at", sa.DateTime(timezone=True),
                              server_default=sa.func.now(), nullable=False),
                    )

    # --------------------------------------------------------------- iso_images
    op.create_table("iso_images",
                    sa.Column("id",          postgresql.UUID(
                        as_uuid=True), primary_key=True),
                    sa.Column("name",        sa.String(128),
                              nullable=False, unique=True),
                    sa.Column("filename",    sa.String(255),
                              nullable=False, unique=True),
                    sa.Column("os_family",   postgresql.ENUM(
                        "LINUX", "WINDOWS",
                        name="os_family_enum", create_type=False), nullable=False),
                    sa.Column("os_version",  sa.String(64),  nullable=False),
                    sa.Column("description", sa.String(512), nullable=True),
                    sa.Column("is_active",   sa.Boolean(),
                              nullable=False, server_default="true"),
                    sa.Column("added_by_id", postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
                    sa.Column("created_at", sa.DateTime(timezone=True),
                              server_default=sa.func.now(), nullable=False),
                    sa.Column("updated_at", sa.DateTime(timezone=True),
                              server_default=sa.func.now(), nullable=False),
                    )

    # -------------------------------------------------------- account_requests
    op.create_table("account_requests",
                    sa.Column("id",               postgresql.UUID(
                        as_uuid=True), primary_key=True),
                    sa.Column("first_name",       sa.String(
                        128), nullable=False),
                    sa.Column("last_name",        sa.String(
                        128), nullable=False),
                    sa.Column("email",            sa.String(
                        255), nullable=False, unique=True),
                    sa.Column("organisation",     sa.String(
                        255), nullable=False),
                    sa.Column("justification",
                              sa.Text(),      nullable=True),
                    sa.Column("status",           postgresql.ENUM(
                        "PENDING", "APPROVED", "REJECTED",
                        name="account_request_status_enum",
                        create_type=False),
                        nullable=False, server_default="PENDING"),
                    sa.Column("reviewed_by_id",   postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
                    sa.Column("reviewed_at",      sa.String(
                        64),  nullable=True),
                    sa.Column("rejection_reason",
                              sa.Text(),      nullable=True),
                    sa.Column("user_id",          postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
                    sa.Column("created_at", sa.DateTime(timezone=True),
                              server_default=sa.func.now(), nullable=False),
                    sa.Column("updated_at", sa.DateTime(timezone=True),
                              server_default=sa.func.now(), nullable=False),
                    )
    op.create_index("ix_account_requests_email", "account_requests", ["email"])

    # -------------------------------------------------------- virtual_machines
    op.create_table("virtual_machines",
                    sa.Column("id",             postgresql.UUID(
                        as_uuid=True), primary_key=True),
                    sa.Column("proxmox_vmid",   sa.Integer(),
                              nullable=False, unique=True),
                    sa.Column("name",           sa.String(
                        128), nullable=False),
                    sa.Column("description",    sa.Text(),      nullable=True),
                    sa.Column("owner_id",       postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
                    sa.Column("node",           postgresql.ENUM(
                        "REM", "RAM", "EMILIA",
                        name="physical_node_enum", create_type=False), nullable=False),
                    sa.Column("vcpu",           sa.Integer(), nullable=False),
                    sa.Column("ram_gb",         sa.Float(),   nullable=False),
                    sa.Column("storage_gb",     sa.Float(),   nullable=False),
                    sa.Column("iso_image_id",   postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("iso_images.id", ondelete="SET NULL"), nullable=True),
                    sa.Column("status",         postgresql.ENUM(
                        "ACTIVE", "STOPPED", "EXPIRED", "SUSPENDED", "PENDING",
                        name="vm_status_enum", create_type=False),
                        nullable=False, server_default="PENDING"),
                    sa.Column("lease_start",    sa.DateTime(
                        timezone=True), nullable=False),
                    sa.Column("lease_end",      sa.DateTime(
                        timezone=True), nullable=False),
                    sa.Column("stopped_at",     sa.DateTime(
                        timezone=True), nullable=True),
                    sa.Column("vlan_id",        sa.Integer(), nullable=True),
                    sa.Column("ip_address",     sa.String(45), nullable=True),
                    sa.Column("ssh_public_key", sa.Text(),    nullable=True),
                    sa.Column("shared_space_gb", sa.Float(),
                              nullable=False, server_default="0.0"),
                    sa.Column("created_at", sa.DateTime(timezone=True),
                              server_default=sa.func.now(), nullable=False),
                    sa.Column("updated_at", sa.DateTime(timezone=True),
                              server_default=sa.func.now(), nullable=False),
                    )
    op.create_index("ix_virtual_machines_owner_id",
                    "virtual_machines", ["owner_id"])
    op.create_index("ix_virtual_machines_proxmox_vmid",
                    "virtual_machines", ["proxmox_vmid"])

    # ------------------------------------------------------------ reservations
    op.create_table("reservations",
                    sa.Column("id",           postgresql.UUID(
                        as_uuid=True), primary_key=True),
                    sa.Column("vm_id",        postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("virtual_machines.id", ondelete="CASCADE"), nullable=False),
                    sa.Column("user_id",      postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
                    sa.Column("start_time",   sa.DateTime(
                        timezone=True), nullable=False),
                    sa.Column("end_time",     sa.DateTime(
                        timezone=True), nullable=False),
                    sa.Column("extended",     sa.Boolean(),
                              nullable=False, server_default="false"),
                    sa.Column("extension_of", postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("reservations.id"), nullable=True),
                    sa.Column("created_at", sa.DateTime(timezone=True),
                              server_default=sa.func.now(), nullable=False),
                    sa.Column("updated_at", sa.DateTime(timezone=True),
                              server_default=sa.func.now(), nullable=False),
                    )
    op.create_index("ix_reservations_vm_id", "reservations", ["vm_id"])

    # --------------------------------------------------------------- audit_logs
    op.create_table("audit_logs",
                    sa.Column("id",          postgresql.UUID(
                        as_uuid=True), primary_key=True),
                    sa.Column("actor_id",    postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
                    sa.Column("action",      postgresql.ENUM(
                        "ACCOUNT_REQUEST_SUBMITTED", "ACCOUNT_APPROVED", "ACCOUNT_REJECTED",
                        "ACCOUNT_SUSPENDED", "ACCOUNT_REACTIVATED", "ACCOUNT_DELETED",
                        "PASSWORD_CHANGED", "PASSWORD_RESET",
                        "LOGIN_SUCCESS", "LOGIN_FAILURE", "LOGOUT", "ACCOUNT_LOCKED",
                        "VM_CREATED", "VM_STARTED", "VM_STOPPED", "VM_FORCE_STOPPED",
                        "VM_DELETED", "VM_ADMIN_DELETED", "VM_MODIFIED", "VM_EXPIRED", "VM_LEASE_EXTENDED",
                        "QUOTA_POLICY_MODIFIED", "QUOTA_OVERRIDE_GRANTED",
                        "ISO_IMAGE_ADDED", "ISO_IMAGE_DISABLED", "FILE_DOWNLOADED",
                        "SECURITY_INCIDENT_CREATED", "SECURITY_INCIDENT_RESOLVED",
                        name="audit_action_enum", create_type=False), nullable=False),
                    sa.Column("target_type", sa.String(64),  nullable=True),
                    sa.Column("target_id",   postgresql.UUID(
                        as_uuid=True), nullable=True),
                    sa.Column("ip_address",  sa.String(45),  nullable=True),
                    sa.Column("metadata",    postgresql.JSONB(),
                              nullable=True),
                    sa.Column("timestamp",   sa.DateTime(
                        timezone=True), nullable=False),
                    )
    op.create_index("ix_audit_logs_actor_id",  "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_target_id", "audit_logs", ["target_id"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])
    op.create_index("ix_audit_logs_action",    "audit_logs", ["action"])

    # ----------------------------------------------------------- login_attempts
    op.create_table("login_attempts",
                    sa.Column("id",             postgresql.UUID(
                        as_uuid=True), primary_key=True),
                    sa.Column("user_id",        postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
                    sa.Column("username_tried", sa.String(64),  nullable=True),
                    sa.Column("success",        sa.Boolean(),
                              nullable=False),
                    sa.Column("ip_address",     sa.String(45),  nullable=True),
                    sa.Column("timestamp",      sa.DateTime(
                        timezone=True), nullable=False),
                    )
    op.create_index("ix_login_attempts_user_id",
                    "login_attempts", ["user_id"])
    op.create_index("ix_login_attempts_timestamp",
                    "login_attempts", ["timestamp"])

    # -------------------------------------------------------- security_incidents
    op.create_table("security_incidents",
                    sa.Column("id",             postgresql.UUID(
                        as_uuid=True), primary_key=True),
                    sa.Column("vm_id",          postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("virtual_machines.id", ondelete="SET NULL"), nullable=True),
                    sa.Column("user_id",        postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
                    sa.Column("incident_type",  postgresql.ENUM(
                        "UNAUTHORIZED_VM_ACCESS", "UNAUTHORIZED_API_ACCESS", "NETWORK_SCAN_DETECTED",
                        "EXPLOIT_TOOL_DETECTED", "CRYPTO_MINING_DETECTED", "SUSPICIOUS_TRAFFIC",
                        "POLICY_VIOLATION",
                        name="incident_type_enum", create_type=False), nullable=False),
                    sa.Column("severity",       postgresql.ENUM(
                        "LOW", "MEDIUM", "HIGH", "CRITICAL",
                        name="incident_severity_enum", create_type=False), nullable=False),
                    sa.Column("status",         postgresql.ENUM(
                        "OPEN", "INVESTIGATING", "RESOLVED",
                        name="incident_status_enum", create_type=False),
                        nullable=False, server_default="OPEN"),
                    sa.Column("description",    sa.Text(), nullable=True),
                    sa.Column("created_at",     sa.DateTime(
                        timezone=True), nullable=False),
                    sa.Column("resolved_at",    sa.DateTime(
                        timezone=True), nullable=True),
                    sa.Column("resolved_by_id", postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
                    )
    op.create_index("ix_security_incidents_vm_id",
                    "security_incidents", ["vm_id"])
    op.create_index("ix_security_incidents_user_id",
                    "security_incidents", ["user_id"])
    op.create_index("ix_security_incidents_created_at",
                    "security_incidents", ["created_at"])

    # --------------------------------------------------------- quota_violations
    op.create_table("quota_violations",
                    sa.Column("id",             postgresql.UUID(
                        as_uuid=True), primary_key=True),
                    sa.Column("vm_id",          postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("virtual_machines.id", ondelete="SET NULL"), nullable=True),
                    sa.Column("user_id",        postgresql.UUID(as_uuid=True),
                              sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
                    sa.Column("violation_type", postgresql.ENUM(
                        "CPU", "RAM", "STORAGE", "SESSION_TIME", "SHARED_SPACE", "VM_COUNT",
                        name="violation_type_enum", create_type=False), nullable=False),
                    sa.Column("sanction_level", postgresql.ENUM(
                        "LEVEL_1", "LEVEL_2", "LEVEL_3",
                        name="sanction_level_enum", create_type=False),
                        nullable=False, server_default="LEVEL_1"),
                    sa.Column("observed_value", sa.Float(), nullable=False),
                    sa.Column("limit_value",    sa.Float(), nullable=False),
                    sa.Column("resolved",       sa.Boolean(),
                              nullable=False, server_default="false"),
                    sa.Column("created_at",     sa.DateTime(
                        timezone=True), nullable=False),
                    )
    op.create_index("ix_quota_violations_vm_id",
                    "quota_violations", ["vm_id"])
    op.create_index("ix_quota_violations_user_id",
                    "quota_violations", ["user_id"])
    op.create_index("ix_quota_violations_created_at",
                    "quota_violations", ["created_at"])


def downgrade() -> None:
    for table in ["quota_violations", "security_incidents", "login_attempts", "audit_logs",
                  "reservations", "virtual_machines", "account_requests", "iso_images",
                  "quota_overrides", "users", "quota_policies", "role_permissions", "roles"]:
        op.drop_table(table)

    for enum in ["quota_violations_enum", "sanction_level_enum", "violation_type_enum",
                 "incident_status_enum", "incident_severity_enum", "incident_type_enum",
                 "audit_action_enum", "vm_status_enum", "physical_node_enum",
                 "account_request_status_enum", "os_family_enum", "user_role_enum"]:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
