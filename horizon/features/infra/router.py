"""
Routes /api/v1/infra — Diagnostic Cluster et Contrôle VM.

Endpoints implémentés :
  GET  /infra/nodes                 → État de tous les nœuds du cluster
  GET  /infra/storage/local/isos    → ISOs présentes sur le stockage 'local'

Endpoints de contrôle VM (aussi accessibles via /vms/{id}/...) :
  POST /vms/{id}/start              → Démarrer une VM (retourne UPID)
  POST /vms/{id}/stop               → Arrêter une VM proprement (retourne UPID)
  GET  /vms/{id}/status             → Statut temps-réel depuis Proxmox

Sécurité :
  - /infra/* : réservé ADMIN et SUPER_ADMIN
  - /vms/{id}/start, stop, status : propriétaire OU admin
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from horizon.features.infra import schemas, service as infra_service
from horizon.infrastructure.database import get_db
from horizon.shared.dependencies import AdminUser, CurrentUser
from horizon.shared.policies.enforcer import PolicyError

router = APIRouter(tags=["Infrastructure & Monitoring"])


# ─────────────────────────── Helper erreur ─────────────────────────────────


def _policy_http(exc: PolicyError):
    """Convertit PolicyError en HTTPException FastAPI."""
    raise HTTPException(status_code=exc.http_status, detail=exc.message)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Diagnostic Cluster — ADMIN uniquement
# ═══════════════════════════════════════════════════════════════════════════


@router.get(
    "/infra/nodes",
    response_model=schemas.ClusterNodesResponse,
    summary="[Admin] État de tous les nœuds du cluster Proxmox",
    description=(
        "Interroge directement l'API Proxmox pour retourner le statut (online/offline), "
        "l'utilisation CPU, la RAM disponible et le nombre de VMs de chaque nœud. "
        "\n\n**Erreur 503** : si le cluster Proxmox est injoignable (réseau 192.168.43.x, "
        "VirtualBox éteint, etc.)."
    ),
    responses={
        200: {"description": "Liste des nœuds avec leurs métriques"},
        503: {"description": "Cluster Proxmox injoignable"},
        403: {"description": "Accès réservé aux admins"},
    },
)
def get_cluster_nodes(
    _admin: AdminUser,          # ← garanti ADMIN / SUPER_ADMIN
):
    """
    GET /api/v1/infra/nodes

    Liste tous les nœuds du cluster avec :
    - statut (online / offline)
    - % CPU utilisé
    - RAM totale / utilisée / libre (en Go)
    - nombre de VMs QEMU actives
    - uptime en heures
    """
    try:
        result = infra_service.get_cluster_nodes()
    except PolicyError as exc:
        _policy_http(exc)

    return schemas.ClusterNodesResponse(**result)


@router.get(
    "/infra/storage/local/isos",
    response_model=schemas.StorageISOListResponse,
    summary="[Admin] ISOs disponibles sur le stockage 'local' de Proxmox",
    description=(
        "Liste tous les fichiers `.iso` présents dans le stockage nommé **`local`** "
        "du nœud Proxmox cible (par défaut : premier nœud online du cluster). "
        "\n\nSeuls les fichiers dont le nom se termine par `.iso` sont retournés. "
        "\n\n**Erreur 503** : cluster Proxmox injoignable."
    ),
    responses={
        200: {"description": "Liste des ISOs avec leur volid, nom et taille"},
        503: {"description": "Cluster Proxmox injoignable"},
        403: {"description": "Accès réservé aux admins"},
    },
)
def get_storage_local_isos(
    _admin: AdminUser,
    node: str | None = Query(
        None,
        description=(
            "Nom du nœud Proxmox à interroger. "
            "Si absent, utilise le premier nœud online du cluster."
        ),
        example="pve1",
    ),
):
    """
    GET /api/v1/infra/storage/local/isos

    Interroge Proxmox : GET /nodes/{node}/storage/local/content?content=iso
    Filtre : uniquement les fichiers se terminant par .iso.

    Retourne pour chaque ISO :
    - volid  : identifiant Proxmox (ex: local:iso/ubuntu-22.04.iso)
    - filename : nom du fichier
    - size_bytes / size_human : taille
    """
    try:
        result = infra_service.get_storage_isos(node=node)
    except PolicyError as exc:
        _policy_http(exc)

    return schemas.StorageISOListResponse(**result)


# ═══════════════════════════════════════════════════════════════════════════
# 2. Contrôle VM temps-réel — Propriétaire ou Admin
# ═══════════════════════════════════════════════════════════════════════════


@router.post(
    "/vms/{vm_id}/start",
    response_model=schemas.VMActionResponse,
    summary="Démarrer une VM sur Proxmox (retourne l'UPID de la tâche)",
    description=(
        "Déclenche le démarrage de la VM directement sur Proxmox et retourne "
        "l'**UPID** de la tâche pour un suivi optionnel. "
        "Le statut BD est mis à jour en `ACTIVE`. "
        "\n\n- **Propriétaire** : peut démarrer ses propres VMs. "
        "\n- **Admin / Super Admin** : peut démarrer n'importe quelle VM. "
        "\n\n**Erreur 409** : VM déjà en cours d'exécution. "
        "\n\n**Erreur 503** : Proxmox injoignable."
    ),
    responses={
        200: {"description": "VM démarrée, UPID retourné"},
        409: {"description": "VM déjà ACTIVE"},
        404: {"description": "VM introuvable"},
        503: {"description": "Proxmox injoignable"},
    },
)
def start_vm(
    vm_id: uuid.UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    POST /api/v1/vms/{vm_id}/start

    Workflow :
      1. Vérification ownership (propriétaire ou admin)
      2. Garde : VM déjà ACTIVE → 409
      3. Appel Proxmox start → UPID
      4. Mise à jour BD status → ACTIVE
      5. Audit log VM_STARTED
    """
    try:
        result = infra_service.start_vm(
            db=db,
            vm_id=vm_id,
            requester_id=current_user.id,
            requester_role=current_user.role.value,
        )
    except PolicyError as exc:
        _policy_http(exc)

    return schemas.VMActionResponse(**result)


@router.post(
    "/vms/{vm_id}/stop",
    response_model=schemas.VMActionResponse,
    summary="Arrêter une VM proprement via Proxmox (ACPI shutdown, retourne l'UPID)",
    description=(
        "Déclenche un **arrêt propre ACPI** (shutdown) de la VM via Proxmox et retourne "
        "l'**UPID** de la tâche. Le statut BD passe à `STOPPED`. "
        "\n\nPour un arrêt forcé (power-cut), utilisez `?force=true`. "
        "\n\n**Erreur 409** : VM déjà arrêtée."
    ),
    responses={
        200: {"description": "Arrêt initié, UPID retourné"},
        409: {"description": "VM déjà STOPPED"},
        503: {"description": "Proxmox injoignable"},
    },
)
def stop_vm(
    vm_id: uuid.UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    force: bool = Query(
        False,
        description="Si true : arrêt forcé (stop) au lieu d'un shutdown ACPI propre.",
    ),
):
    """
    POST /api/v1/vms/{vm_id}/stop

    Workflow :
      1. Vérification ownership
      2. Garde : VM déjà STOPPED → 409
      3. Appel Proxmox shutdown (ACPI) ou stop (force)
      4. Mise à jour BD status → STOPPED
      5. Audit log VM_STOPPED ou VM_FORCE_STOPPED
    """
    try:
        result = infra_service.stop_vm_realtime(
            db=db,
            vm_id=vm_id,
            requester_id=current_user.id,
            requester_role=current_user.role.value,
            force=force,
        )
    except PolicyError as exc:
        _policy_http(exc)

    return schemas.VMActionResponse(**result)


@router.get(
    "/vms/{vm_id}/status",
    response_model=schemas.VMProxmoxStatusResponse,
    summary="Statut temps-réel d'une VM — interroge directement Proxmox",
    description=(
        "Récupère l'état **courant** de la VM directement depuis Proxmox "
        "(pas depuis le cache en base de données). "
        "Garantit la synchronisation avec l'interface web Proxmox. "
        "\n\nRenvoie également les métriques en temps réel si la VM est en cours "
        "d'exécution : CPU, RAM, I/O disque, trafic réseau, IP (via QEMU Guest Agent). "
        "\n\nLe statut BD est **auto-synchronisé** si une incohérence est détectée."
    ),
    responses={
        200: {"description": "Statut complet + métriques temps-réel"},
        404: {"description": "VM introuvable"},
        503: {"description": "Proxmox injoignable"},
    },
)
def get_vm_status(
    vm_id: uuid.UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    GET /api/v1/vms/{vm_id}/status

    Interroge directement Proxmox :
      GET /nodes/{node}/qemu/{vmid}/status/current

    Auto-synchronise le statut BD si Proxmox et BD divergent.
    Tente de récupérer l'IP via QEMU Guest Agent (non bloquant).
    """
    try:
        result = infra_service.get_vm_proxmox_status(
            db=db,
            vm_id=vm_id,
            requester_id=current_user.id,
            requester_role=current_user.role.value,
        )
    except PolicyError as exc:
        _policy_http(exc)

    return schemas.VMProxmoxStatusResponse(**result)
