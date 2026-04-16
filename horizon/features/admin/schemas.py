"""Schemas Pydantic — Administration (v2)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ─────────────────────── ISO Admin ────────────────────────────────────────

class ISOValidateRequest(BaseModel):
    """PATCH /admin/isos/{id}/validate"""
    note: str | None = Field(None, max_length=512, description="Note de validation optionnelle")


class ISORejectRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=512)


class ISOAdminResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    name: str
    filename: str
    os_family: str
    os_version: str
    status: str
    source_url: str | None
    proxmox_node: str | None
    proxmox_storage: str | None
    proxmox_upid: str | None
    size_bytes: int | None
    error_message: str | None
    created_at: datetime
    created_by_id: UUID | None

    @classmethod
    def _enum_str(cls, v):
        return v.value if hasattr(v, "value") else v

    from pydantic import field_validator

    @field_validator("os_family", "status", mode="before")
    @classmethod
    def enum_to_str(cls, v):
        return v.value if hasattr(v, "value") else v


class ISOAdminListResponse(BaseModel):
    items: list[ISOAdminResponse]
    total: int


# ─────────────────────── Cluster Monitoring ───────────────────────────────

class NodeInfoResponse(BaseModel):
    name: str
    cpu_usage_pct: float
    mem_used_gb: float
    mem_total_gb: float
    mem_free_gb: float
    vm_count: int


class ClusterSummaryResponse(BaseModel):
    nodes: list[NodeInfoResponse]
    total_nodes: int
    total_vms: int


# ─────────────────────── Node Mappings (conservé) ─────────────────────────

class ProxmoxNodeMappingResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    proxmox_node_name: str
    description: str | None = None


class ProxmoxNodeMappingListResponse(BaseModel):
    items: list[ProxmoxNodeMappingResponse]


# ─────────────────────── VM Admin ─────────────────────────────────────────

class AdminVMResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    proxmox_vmid: int
    name: str
    status: str
    proxmox_node: str
    vcpu: int
    ram_gb: float
    storage_gb: float
    owner_id: UUID
    lease_start: datetime
    lease_end: datetime

    from pydantic import field_validator

    @field_validator("status", mode="before")
    @classmethod
    def status_str(cls, v):
        return v.value if hasattr(v, "value") else v


class AdminVMListResponse(BaseModel):
    items: list[AdminVMResponse]
    total: int


class AdminForceStopResponse(BaseModel):
    message: str
    upid: str | None = None


class ForceStopRequest(BaseModel):
    reason: str | None = None


# ─────────────────────── Quota ────────────────────────────────────────────

class QuotaOverrideRequest(BaseModel):
    user_id: str
    max_vcpu_per_vm: int | None = None
    max_ram_gb_per_vm: float | None = None
    max_storage_gb_per_vm: float | None = None
    max_simultaneous_vms: int | None = None
    max_session_duration_hours: int | None = None
    reason: str | None = None


class QuotaOverrideMessageResponse(BaseModel):
    message: str


# ─────────────────────── Audit / Incidents ────────────────────────────────

class AuditLogResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    timestamp: datetime
    action: str
    target_type: str | None
    target_id: UUID | None
    user_id: UUID | None

    from pydantic import field_validator

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
    status: str
    created_at: datetime

    from pydantic import field_validator

    @field_validator("status", mode="before")
    @classmethod
    def status_str(cls, v):
        return v.value if hasattr(v, "value") else v


class SecurityIncidentListResponse(BaseModel):
    items: list[SecurityIncidentResponse]


class QuotaViolationResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    resolved: bool
    created_at: datetime


class QuotaViolationListResponse(BaseModel):
    items: list[QuotaViolationResponse]


# ─────────────────────── Proxmox raw ops ──────────────────────────────────

class ProxmoxOperationResponse(BaseModel):
    message: str
    upid: str | None = None


class ProxmoxQemuListResponse(BaseModel):
    node: str
    vms: list[dict]


class ProxmoxVmStatusResponse(BaseModel):
    proxmox_vmid: int
    raw_status: dict


class IsoProxmoxTemplateResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    iso_image_id: UUID
    proxmox_template_vmid: int


class IsoProxmoxTemplateListResponse(BaseModel):
    items: list[IsoProxmoxTemplateResponse]


class IsoProxmoxTemplateCreate(BaseModel):
    iso_image_id: str
    proxmox_template_vmid: int


class IsoProxmoxTemplatePatch(BaseModel):
    proxmox_template_vmid: int | None = None
