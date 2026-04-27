"""Schémas Pydantic - administration."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AdminVMRowResponse(BaseModel):
    id: UUID
    proxmox_vmid: int
    name: str
    owner_username: str | None = None
    node: str
    vcpu: int
    ram_gb: float
    storage_gb: float
    status: str
    lease_end: datetime
    ip_address: str | None = None


class AdminVMListResponse(BaseModel):
    items: list[AdminVMRowResponse]


class ForceStopRequest(BaseModel):
    reason: str | None = Field(default="Arrêt forcé par administrateur")


class QuotaOverrideRequest(BaseModel):
    user_id: str
    max_vcpu_per_vm: int | None = None
    max_ram_gb_per_vm: float | None = None
    max_storage_gb_per_vm: float | None = None
    max_shared_space_gb: float | None = None
    max_simultaneous_vms: int | None = None
    max_session_duration_hours: int | None = None
    reason: str


class QuotaOverrideMessageResponse(BaseModel):
    message: str


class AdminForceStopResponse(BaseModel):
    message: str


class AuditLogResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    actor_id: UUID | None
    action: str
    target_type: str | None
    target_id: UUID | None
    ip_address: str | None
    log_metadata: dict[str, Any] | None = None
    timestamp: datetime

    @field_validator("action", mode="before")
    @classmethod
    def action_str(cls, v):
        return v.value if hasattr(v, "value") else v


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    limit: int
    offset: int


class SecurityIncidentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    vm_id: UUID | None
    user_id: UUID | None
    incident_type: str
    severity: str
    status: str
    description: str | None
    created_at: datetime
    resolved_at: datetime | None
    resolved_by_id: UUID | None

    @field_validator("incident_type", "severity", "status", mode="before")
    @classmethod
    def enum_str(cls, v):
        return v.value if hasattr(v, "value") else v


class SecurityIncidentListResponse(BaseModel):
    items: list[SecurityIncidentResponse]


class QuotaViolationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    vm_id: UUID | None
    user_id: UUID
    violation_type: str
    sanction_level: str
    observed_value: float
    limit_value: float
    resolved: bool
    created_at: datetime

    @field_validator("violation_type", "sanction_level", mode="before")
    @classmethod
    def enum_str(cls, v):
        return v.value if hasattr(v, "value") else v


class QuotaViolationListResponse(BaseModel):
    items: list[QuotaViolationResponse]


class ProxmoxOperationResponse(BaseModel):
    status: str
    message: str


class ProxmoxQemuListResponse(BaseModel):
    count: int
    items: list[dict[str, Any]]


class ProxmoxVmStatusResponse(BaseModel):
    data: dict[str, Any]


class ProxmoxNodeMappingResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    physical_node: str
    proxmox_node_name: str


class ProxmoxNodeMappingListResponse(BaseModel):
    items: list[ProxmoxNodeMappingResponse]


class ProxmoxNodeMappingCreate(BaseModel):
    physical_node: str = Field(..., description="REM, RAM ou EMILIA")
    proxmox_node_name: str = Field(..., min_length=1, max_length=64)


class ProxmoxNodeMappingPatch(BaseModel):
    proxmox_node_name: str = Field(..., min_length=1, max_length=64)


class IsoProxmoxTemplateResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    iso_image_id: UUID
    iso_name: str | None = None
    proxmox_template_vmid: int


class IsoProxmoxTemplateListResponse(BaseModel):
    items: list[IsoProxmoxTemplateResponse]


class IsoProxmoxTemplateCreate(BaseModel):
    iso_image_id: UUID
    proxmox_template_vmid: int = Field(..., ge=1)


class IsoProxmoxTemplatePatch(BaseModel):
    proxmox_template_vmid: int = Field(..., ge=1)


class ReservationRowResponse(BaseModel):
    id: UUID
    vm_name: str
    user_full_name: str
    user_email: str
    os_name: str
    vcpu: int
    ram_gb: float
    storage_gb: float
    duration_hours: int
    status: str
    created_at: datetime


class ReservationListResponse(BaseModel):
    items: list[ReservationRowResponse]


class ISOImageResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    name: str
    filename: str
    os_family: str
    os_version: str
    description: str | None
    is_active: bool
    created_at: datetime


class ISOImageListResponse(BaseModel):
    items: list[ISOImageResponse]


class ISOImageCreate(BaseModel):
    name: str
    filename: str
    os_family: str
    os_version: str
    description: str | None = None

    @field_validator("os_family", mode="before")
    @classmethod
    def normalise_os_family(cls, v: str) -> str:
        """Force la valeur en majuscule pour correspondre à l'enum os_family_enum en DB."""
        return v.upper()


class ProxmoxNodeSummary(BaseModel):
    name: str
    status: str
    cpu: float
    memory: dict[str, Any]
    vms_count: int


class ProxmoxSummaryResponse(BaseModel):
    nodes: list[ProxmoxNodeSummary]
    total_vms: int
    active_vms: int
    total_cpus: int
    used_cpus: int
    total_memory: int
    used_memory: int


class PrepareTemplateRequest(BaseModel):
    vmid: int = Field(..., ge=100)
    node: str
    storage: str = "local"
    iso_storage: str | None = Field(
        default=None,
        description="Stockage où se trouve l'ISO (si différent du stockage disque)",
    )
    iso_filename: str
    name: str = "template-prepare"
    vcpu: int = 2
    ram_mb: int = 2048
    storage_gb: int = 20


class ProxmoxCreateVMRequest(BaseModel):
    vmid: int = Field(..., ge=100)
    node: str
    storage: str = "local"
    iso_storage: str | None = Field(default=None)
    iso_filename: str
    name: str
    vcpu: int = 1
    ram_mb: int = 1024
    storage_gb: int = 10
    net0: str = "virtio,bridge=vmbr0"


# ---------------------------------------------------------------------------
# TinyVM — micro-VM optimisées (Alpine Linux ou équivalent léger)
# ---------------------------------------------------------------------------

TINYVM_VCPU_DEFAULT = 1
TINYVM_RAM_MB_DEFAULT = 512
TINYVM_STORAGE_GB_DEFAULT = 4
TINYVM_ISO_DEFAULT = "alpine-standard-latest.iso"
TINYVM_ISO_STORAGE_DEFAULT = "local"
TINYVM_NET0_DEFAULT = "virtio,bridge=vmbr0"


class TinyVMCreate(BaseModel):
    """
    Paramètres de création d'une TinyVM (micro-VM Alpine optimisée).

    Les ressources sont volontairement plafonnées côté schéma pour empêcher
    qu'un administrateur crée accidentellement une VM "full-size" via cet endpoint.
    """

    vmid: int = Field(..., ge=100, description="VMID Proxmox cible (≥ 100)")
    node: str = Field(..., description="Nœud Proxmox cible (ex. pve1)")
    name: str = Field(
        default="tinyvm",
        min_length=1,
        max_length=64,
        description="Nom de la VM Proxmox",
    )
    storage: str = Field(
        default="local",
        description="Stockage Proxmox pour le disque de la VM",
    )
    iso_storage: str = Field(
        default=TINYVM_ISO_STORAGE_DEFAULT,
        description="Stockage Proxmox où se trouve l'ISO Alpine",
    )
    iso_filename: str = Field(
        default=TINYVM_ISO_DEFAULT,
        description="Nom du fichier ISO à monter (doit être présent sur le stockage iso_storage)",
    )
    vcpu: int = Field(
        default=TINYVM_VCPU_DEFAULT,
        ge=1,
        le=2,
        description="Nombre de vCPUs (max 2 pour une TinyVM)",
    )
    ram_mb: int = Field(
        default=TINYVM_RAM_MB_DEFAULT,
        ge=256,
        le=1024,
        description="RAM en Mo (256 Mo – 1 Go pour une TinyVM)",
    )
    storage_gb: int = Field(
        default=TINYVM_STORAGE_GB_DEFAULT,
        ge=2,
        le=10,
        description="Taille du disque en Go (2 – 10 Go pour une TinyVM)",
    )
    net0: str = Field(
        default=TINYVM_NET0_DEFAULT,
        description="Paramètre réseau net0 Proxmox",
    )
    start_after_create: bool = Field(
        default=False,
        description="Démarrer la VM immédiatement après sa création",
    )


class TinyVMResponse(BaseModel):
    """Réponse après création d'une TinyVM."""

    vmid: int
    node: str
    name: str
    status: str
    message: str
    proxmox_task: dict[str, Any] | None = None