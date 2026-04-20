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
    iso_storage: str | None = Field(default=None, description="Stockage où se trouve l'ISO (si différent du stockage disque)")
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

