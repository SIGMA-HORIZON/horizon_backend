"""
Schemas Pydantic — Infrastructure / Diagnostic Cluster.

Couvre :
  - Nœuds du cluster (statut, CPU, RAM)
  - ISOs présentes sur le stockage local du nœud Proxmox
  - Statut temps-réel d'une VM (direct Proxmox)
  - Réponse start/stop avec UPID
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ─────────────────────────── Cluster / Nœuds ───────────────────────────────


class NodeStatusResponse(BaseModel):
    """
    Informations détaillées sur un nœud Proxmox.
    Retournées par GET /infra/nodes.
    """
    name: str = Field(..., description="Nom du nœud (ex: pve1)")
    status: str = Field(..., description="'online' ou 'offline'")
    cpu_usage_pct: float = Field(..., description="Utilisation CPU en % (0–100)")
    mem_used_gb: float = Field(..., description="RAM utilisée en Go")
    mem_total_gb: float = Field(..., description="RAM totale en Go")
    mem_free_gb: float = Field(..., description="RAM disponible en Go")
    vm_count: int = Field(..., description="Nombre de VMs QEMU sur ce nœud")
    uptime_hours: float | None = Field(None, description="Uptime du nœud en heures")


class ClusterNodesResponse(BaseModel):
    """Réponse complète GET /infra/nodes."""
    nodes: list[NodeStatusResponse]
    total_nodes: int
    nodes_online: int
    nodes_offline: int
    total_vms: int
    proxmox_host: str = Field(..., description="Adresse du cluster Proxmox interrogé")


# ─────────────────────────── ISOs Stockage ─────────────────────────────────


class StorageISOItem(BaseModel):
    """Un fichier ISO présent sur le stockage Proxmox."""
    volid: str = Field(..., description="Identifiant volume Proxmox (ex: local:iso/ubuntu.iso)")
    filename: str = Field(..., description="Nom du fichier ISO")
    size_bytes: int = Field(0, description="Taille en octets")
    size_human: str = Field(..., description="Taille lisible (ex: 1.2 Go)")


class StorageISOListResponse(BaseModel):
    """Réponse GET /infra/storage/local/isos."""
    node: str = Field(..., description="Nœud Proxmox interrogé")
    storage: str = Field(..., description="Nom du stockage (toujours 'local')")
    isos: list[StorageISOItem]
    total: int


# ─────────────────────────── Contrôle VM ───────────────────────────────────


class VMProxmoxStatusResponse(BaseModel):
    """
    Statut temps-réel d'une VM directement depuis Proxmox.
    Retourné par GET /vms/{id}/status.
    """
    vm_id: UUID = Field(..., description="UUID Horizon de la VM")
    proxmox_vmid: int = Field(..., description="VMID Proxmox")
    proxmox_node: str = Field(..., description="Nœud Proxmox hébergeant la VM")
    proxmox_status: str = Field(
        ...,
        description="Statut Proxmox brut : 'running', 'stopped', 'paused', 'suspended'",
    )
    horizon_status: str = Field(..., description="Statut Horizon de la VM (ACTIVE, STOPPED…)")
    uptime_seconds: int | None = Field(None, description="Uptime en secondes (si running)")
    cpu_usage_pct: float | None = Field(None, description="Usage CPU actuel en %")
    mem_used_mb: int | None = Field(None, description="RAM utilisée en Mo")
    mem_total_mb: int | None = Field(None, description="RAM totale en Mo")
    disk_read_bytes: int | None = Field(None, description="Lecture disque (octets)")
    disk_write_bytes: int | None = Field(None, description="Écriture disque (octets)")
    net_in_bytes: int | None = Field(None, description="Réseau entrant (octets)")
    net_out_bytes: int | None = Field(None, description="Réseau sortant (octets)")
    ip_address: str | None = Field(None, description="IP reportée par QEMU Guest Agent")


class VMActionResponse(BaseModel):
    """
    Réponse d'une action start / stop sur une VM.
    Contient l'UPID Proxmox pour un suivi de tâche.
    """
    vm_id: UUID = Field(..., description="UUID Horizon de la VM")
    proxmox_vmid: int
    proxmox_node: str
    action: str = Field(..., description="'start' ou 'stop'")
    upid: str = Field(..., description="UPID de la tâche Proxmox")
    message: str
