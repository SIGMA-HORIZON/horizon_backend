"""
Schemas Pydantic — Machines Virtuelles (v2).

Couvre :
- Parcours A : templates + deploy-template (Cloud-Init)
- Parcours B : create-manual
- ISO : download, status, list
- Opérations communes : start/stop/delete/extend
"""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# ─────────────────────────── Helpers de validation ─────────────────────────

_VM_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\-]{1,61}[a-zA-Z0-9]$")
_SSH_KEY_RE = re.compile(r"^(ssh-(rsa|ed25519|ecdsa)|ecdsa-sha2-nistp\d+) [A-Za-z0-9+/=]+")


def _validate_vm_name(v: str) -> str:
    if not _VM_NAME_RE.match(v):
        raise ValueError(
            "Le nom de VM doit contenir 3–63 caractères alphanumériques ou tirets, "
            "commencer et finir par un caractère alphanumérique."
        )
    return v


# ─────────────────────────── Parcours A : Templates ─────────────────────────

class TemplateResponse(BaseModel):
    vmid: int
    name: str
    node: str
    status: str | None
    mem_mb: int
    cpus: int | None
    disk_gb: float
    tags: str


class TemplateListResponse(BaseModel):
    items: list[TemplateResponse]
    total: int


class CloudInitConfig(BaseModel):
    """Paramètres Cloud-Init injectés après le clone."""
    user: str = Field(..., min_length=1, max_length=64, description="Nom d'utilisateur Cloud-Init")
    ssh_key: str | None = Field(None, description="Clé publique SSH (recommandée)")
    password: str | None = Field(None, min_length=8, description="Mot de passe (déconseillé si SSH disponible)")
    ip_config: str | None = Field(
        None,
        description="Config IP Cloud-Init. Ex: 'ip=dhcp' ou 'ip=192.168.1.10/24,gw=192.168.1.1'",
    )

    @field_validator("ssh_key")
    @classmethod
    def validate_ssh_key(cls, v: str | None) -> str | None:
        if v is not None and not _SSH_KEY_RE.match(v.strip()):
            raise ValueError("Format de clé SSH invalide. Attendu: ssh-rsa/ed25519/ecdsa <base64>")
        return v.strip() if v else v

    @model_validator(mode="after")
    def require_auth(self) -> "CloudInitConfig":
        if not self.ssh_key and not self.password:
            raise ValueError("Au moins une méthode d'authentification (ssh_key ou password) est requise.")
        return self


class DeployTemplateRequest(BaseModel):
    """POST /api/v1/vms/deploy-template"""
    template_vmid: int = Field(..., gt=0, description="VMID du template Proxmox")
    vm_name: str = Field(..., description="Nom de la nouvelle VM")
    session_hours: int = Field(..., ge=1, description="Durée de la session en heures")
    memory_mb: int = Field(2048, ge=512, description="RAM en Mo")
    cores: int = Field(2, ge=1, le=64, description="Nombre de cœurs vCPU")
    disk_storage: str = Field("local-lvm", description="Stockage cible pour le clone")
    net0: str = Field("virtio,bridge=vmbr0,firewall=1", description="Config réseau (format Proxmox)")
    node_strategy: str = Field("least_vms", description="Stratégie de sélection de nœud")
    cloud_init: CloudInitConfig

    @field_validator("vm_name")
    @classmethod
    def name_valid(cls, v: str) -> str:
        return _validate_vm_name(v)

    @field_validator("node_strategy")
    @classmethod
    def strategy_valid(cls, v: str) -> str:
        if v not in ("least_vms", "most_ram"):
            raise ValueError("node_strategy doit être 'least_vms' ou 'most_ram'")
        return v


# ─────────────────────────── Parcours B : Manuel ───────────────────────────

class CreateManualRequest(BaseModel):
    """POST /api/v1/vms/create-manual"""
    vm_name: str
    session_hours: int = Field(..., ge=1)
    vcpu: int = Field(..., ge=1, le=64)
    ram_gb: float = Field(..., gt=0)
    storage_gb: int = Field(..., ge=1)
    disk_storage: str = Field("local-lvm")
    iso_id: UUID = Field(..., description="UUID de l'ISO validée en base")
    net0: str = Field("virtio,bridge=vmbr0,firewall=1")
    bios: str = Field("seabios")
    ostype: str = Field("l26")
    node_strategy: str = Field("least_vms")
    description: str | None = None

    @field_validator("vm_name")
    @classmethod
    def name_valid(cls, v: str) -> str:
        return _validate_vm_name(v)

    @field_validator("bios")
    @classmethod
    def bios_valid(cls, v: str) -> str:
        if v not in ("seabios", "ovmf"):
            raise ValueError("bios doit être 'seabios' ou 'ovmf'")
        return v

    @field_validator("ram_gb")
    @classmethod
    def ram_min(cls, v: float) -> float:
        if v < 0.5:
            raise ValueError("ram_gb minimum : 0.5")
        return v


# ─────────────────────────── VM Response ───────────────────────────────────

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
    creation_mode: str
    proxmox_node: str
    lease_start: datetime
    lease_end: datetime
    ip_address: str | None
    last_upid: str | None

    @field_validator("status", "creation_mode", mode="before")
    @classmethod
    def enum_to_str(cls, v):
        return v.value if hasattr(v, "value") else v


class VMListResponse(BaseModel):
    items: list[VMResponse]
    total: int


class VMExtendRequest(BaseModel):
    additional_hours: int = Field(..., ge=1)


class VMStopResponse(BaseModel):
    message: str
    upid: str | None = None


class SSHKeyDownloadResponse(BaseModel):
    ssh_public_key: str
    warning: str


# ─────────────────────────── ISO Schemas ───────────────────────────────────

class ISODownloadRequest(BaseModel):
    """POST /api/v1/vms/isos/download"""
    url: str = Field(..., description="URL directe de l'ISO (http/https)")
    filename: str = Field(..., min_length=3, description="Nom de fichier cible sur Proxmox")
    name: str = Field(..., min_length=2, max_length=128, description="Nom lisible")
    os_family: str = Field(..., description="LINUX | WINDOWS | OTHER")
    os_version: str = Field(..., min_length=1, max_length=64)
    description: str | None = None
    storage: str = Field("local", description="Stockage Proxmox cible")
    checksum: str | None = None
    checksum_algorithm: str = Field("sha256")

    @field_validator("url")
    @classmethod
    def url_valid(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("L'URL doit commencer par http:// ou https://")
        return v

    @field_validator("filename")
    @classmethod
    def filename_valid(cls, v: str) -> str:
        if not v.endswith(".iso"):
            raise ValueError("Le filename doit se terminer par .iso")
        if "/" in v or ".." in v:
            raise ValueError("Le filename ne peut pas contenir '/' ou '..'")
        return v

    @field_validator("os_family")
    @classmethod
    def os_family_valid(cls, v: str) -> str:
        if v.upper() not in ("LINUX", "WINDOWS", "OTHER"):
            raise ValueError("os_family doit être LINUX, WINDOWS ou OTHER")
        return v.upper()

    @field_validator("checksum_algorithm")
    @classmethod
    def algo_valid(cls, v: str) -> str:
        if v not in ("md5", "sha1", "sha224", "sha256", "sha384", "sha512"):
            raise ValueError("Algorithme de checksum non supporté")
        return v


class ISOResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    name: str
    filename: str
    os_family: str
    os_version: str
    description: str | None
    status: str
    source_url: str | None
    proxmox_node: str | None
    proxmox_storage: str | None
    size_bytes: int | None
    created_at: datetime

    @field_validator("os_family", "status", mode="before")
    @classmethod
    def enum_to_str(cls, v):
        return v.value if hasattr(v, "value") else v


class ISOListResponse(BaseModel):
    items: list[ISOResponse]
    total: int


class ISOStatusResponse(BaseModel):
    """Réponse de l'endpoint de polling statut téléchargement."""
    iso_id: UUID
    filename: str
    status: str
    upid: str | None
    proxmox_task_status: str | None = None
    proxmox_task_exit: str | None = None
    progress_pct: int | None = None
    error_message: str | None = None


# ─────────────────────────── Cluster / Nœuds ───────────────────────────────

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
