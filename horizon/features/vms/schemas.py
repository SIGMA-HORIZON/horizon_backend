"""Schémas Pydantic - VMs utilisateur."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class VMCreateRequest(BaseModel):
    name: str
    iso_image_id: str = Field(..., alias="os")
    vcpu: int = Field(..., alias="cpu")
    ram_gb: float = Field(..., alias="ram")
    storage_gb: float = Field(..., alias="storage")
    session_hours: int = 2  # Par défaut 2 heures si non précisé par le frontend
    description: str | None = None

    model_config = {
        "populate_by_name": True,  # Permet d'utiliser soit le nom réel soit l'alias
    }

    @field_validator("vcpu")
    @classmethod
    def vcpu_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("vcpu doit être >= 1")
        return v

    @field_validator("ram_gb", "storage_gb")
    @classmethod
    def positive_float(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("La valeur doit être positive")
        return v


class VMUpdateRequest(BaseModel):
    vcpu: int | None = None
    ram_gb: float | None = None
    storage_gb: float | None = None


class VMResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    proxmox_vmid: int
    name: str
    description: str | None
    vcpu: int
    ram_gb: float
    storage_gb: float
    status: str
    lease_start: datetime
    lease_end: datetime
    ip_address: str | None

    @field_validator("status", mode="before")
    @classmethod
    def status_str(cls, v):
        return v.value if hasattr(v, "value") else v


class VMListResponse(BaseModel):
    items: list[VMResponse]


class VMExtendRequest(BaseModel):
    additional_hours: int = Field(..., ge=1)


class VMStopMessageResponse(BaseModel):
    message: str


class SSHKeyDownloadResponse(BaseModel):
    ssh_public_key: str
    warning: str
