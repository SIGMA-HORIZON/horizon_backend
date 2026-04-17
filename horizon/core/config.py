"""
Horizon — Configuration (Pydantic v2 BaseSettings) — v2.

Nouveaux paramètres Proxmox :
  PROXMOX_NODE_STRATEGY   : stratégie de sélection nœud ("least_vms" | "most_ram")
  PROXMOX_ISO_STORAGE     : stockage par défaut pour les ISOs (ex: "local")
  PROXMOX_DISK_STORAGE    : stockage par défaut pour les disques VM (ex: "local-lvm")
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "changeme"
    APP_DEBUG: bool = True

    JWT_SECRET_KEY: str = "changeme-jwt"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DATABASE_URL: str = (
        "postgresql+psycopg2://horizon_user:horizon_pass@localhost:5432/horizon_db"
    )
    REDIS_URL: str = "redis://localhost:6379/0"

    EMAIL_MODE: str = "mock"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    EMAIL_FROM: str = "no-reply@horizon.enspy.cm"
    EMAIL_FROM_NAME: str = "Horizon ENSPY"

    BCRYPT_ROUNDS: int = 12
    ENFORCE_HTTPS: bool = False

    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15
    ADMIN_ALERT_ATTEMPTS: int = 10
    PASSWORD_MIN_LENGTH: int = 10
    TEMP_PASSWORD_LENGTH: int = 12

    INACTIVITY_SUSPENSION_DAYS: int = 90
    INACTIVITY_WARNING_DAYS: int = 83
    DELETION_AFTER_SUSPENSION_DAYS: int = 30

    VM_EXPIRY_WARNING_MINUTES: int = 30
    VM_AUTO_DELETE_AFTER_STOPPED_DAYS: int = 7
    SHARED_SPACE_RETENTION_HOURS: int = 24
    SHARED_SPACE_PURGE_WARNING_HOURS: int = 2

    VM_INACTIVITY_ALERT_HOURS: int = 2
    AUDIT_LOG_RETENTION_DAYS: int = 90
    MONITORING_INTERVAL_SECONDS: int = 60

    DEFAULT_MAX_VCPU_PER_VM: int = 2
    DEFAULT_MAX_RAM_GB: float = 2.0
    DEFAULT_MAX_STORAGE_GB: float = 20.0
    DEFAULT_MAX_SHARED_SPACE_GB: float = 5.0
    DEFAULT_MAX_SIMULTANEOUS_VMS: int = 2
    DEFAULT_MAX_SESSION_HOURS: int = 4

    HARD_LIMIT_VCPU: int = 8
    HARD_LIMIT_RAM_GB: float = 16.0
    HARD_LIMIT_STORAGE_GB: float = 100.0
    HARD_LIMIT_SIMULTANEOUS_VMS: int = 5
    HARD_LIMIT_SESSION_HOURS: int = 72
    HARD_LIMIT_SHARED_SPACE_GB: float = 20.0

    # ── Proxmox ────────────────────────────────────────────────────────────
    PROXMOX_ENABLED: bool = False
    PROXMOX_HOST: str = ""
    PROXMOX_USER: str = ""          # ex: horizon@pve ou horizon@pam
    PROXMOX_TOKEN_ID: str = ""      # nom du token API (ex: "horizon-token")
    PROXMOX_TOKEN_SECRET: str = ""  # valeur UUID du token
    PROXMOX_PASSWORD: str | None = None
    PROXMOX_VERIFY_SSL: bool = False

    # Sélection de nœud automatique
    PROXMOX_NODE_STRATEGY: str = "least_vms"   # "least_vms" | "most_ram"

    # Stockages par défaut
    PROXMOX_ISO_STORAGE: str = "local"          # stockage des ISOs
    PROXMOX_DISK_STORAGE: str = "local-lvm"     # stockage disques VM

    # Réseau
    PROXMOX_NET0_TEMPLATE: str = "virtio,bridge=vmbr0,firewall=1"

    # Fallback VMID (si next_free_vmid Proxmox indisponible)
    PROXMOX_VMID_BASE: int = 200


@lru_cache
def get_settings() -> Settings:
    return Settings()
