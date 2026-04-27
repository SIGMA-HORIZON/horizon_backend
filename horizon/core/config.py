"""
Horizon - Configuration (Pydantic v2 BaseSettings)
Politiques POL-SIGMA-HORIZON-v1.0
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
        "postgresql+psycopg2://horizon:horizon@localhost:5432/horizon"
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

    # Proxmox - Integrated Configuration
    PROXMOX_ENABLED: bool = False
    PROXMOX_HOST: str = ""
    PROXMOX_PORT: int = 8006
    PROXMOX_USER: str = ""
    PROXMOX_TOKEN_NAME: str = ""
    PROXMOX_TOKEN_VALUE: str = ""
    PROXMOX_VERIFY_SSL: bool = False
    PROXMOX_NODE: str = ""
    PROXMOX_NET0_TEMPLATE: str = "virtio,bridge=vmbr0"
    PROXMOX_VLAN_ISOLATION: bool = True
    PROXMOX_TIMEOUT: int = 120
    # If true, Horizon will attempt to delete VMs from Proxmox and the DB immediately when they expire
    PROXMOX_DELETE_ON_EXPIRY: bool = True
    # root@pam credentials for VNC WebSocket session authentication (API tokens cannot auth vncwebsocket)
    PROXMOX_ROOT_USER: str = "root@pam"
    PROXMOX_ROOT_PASSWORD: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
