"""
Routes /api/v1/vms — Machines Virtuelles (v2).

Parcours A : GET /templates, POST /deploy-template
Parcours B : POST /create-manual
ISOs       : GET /isos, POST /isos/download, GET /isos/{id}/status, WS /isos/{id}/ws-status
Commun     : GET /, GET /{id}, POST /{id}/stop, DELETE /{id}, POST /{id}/extend
"""

from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from horizon.features.vms import schemas
from horizon.features.vms import service as vm_service
from horizon.infrastructure.database import get_db
from horizon.shared.audit_service import log_action
from horizon.shared.dependencies import CurrentUser
from horizon.shared.models import AuditAction, VirtualMachine
from horizon.shared.policies.enforcer import PolicyError, enforce_vm_ownership

router = APIRouter(prefix="/vms", tags=["Machines Virtuelles"])


# ──────────────────────── Gestion des erreurs Proxmox ─────────────────────

def _policy_to_http(exc: PolicyError):
    from fastapi import HTTPException
    status = getattr(exc, 'http_status', 400)
    message = getattr(exc, 'message', str(exc))
    raise HTTPException(status_code=status, detail=message)


# ─────────────────────────── Templates (Parcours A) ───────────────────────

@router.get(
    "/templates",
    response_model=schemas.TemplateListResponse,
    summary="[Parcours A] Lister les templates disponibles sur le cluster",
)
def list_templates(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    node: str | None = Query(None, description="Filtrer par nœud Proxmox"),
    os_filter: str | None = Query(None, description="Filtrer par nom (ex: ubuntu)"),
):
    try:
        items = vm_service.list_templates(db, node=node, os_filter=os_filter)
    except PolicyError as exc:
        _policy_to_http(exc)
    return schemas.TemplateListResponse(
        items=[schemas.TemplateResponse(**t) for t in items],
        total=len(items),
    )


@router.post(
    "/deploy-template",
    response_model=schemas.VMResponse,
    status_code=201,
    summary="[Parcours A] Déployer une VM depuis un template avec Cloud-Init",
)
def deploy_template(
    body: schemas.DeployTemplateRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    try:
        vm = vm_service.deploy_from_template(db, current_user.id, body.model_dump())
    except PolicyError as exc:
        _policy_to_http(exc)
    return schemas.VMResponse.model_validate(vm)


# ─────────────────────────── Création Manuelle (Parcours B) ───────────────

@router.post(
    "/create-manual",
    response_model=schemas.VMResponse,
    status_code=201,
    summary="[Parcours B] Créer une VM manuelle avec ISO",
)
def create_manual(
    body: schemas.CreateManualRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    try:
        vm = vm_service.create_manual(db, current_user.id, body.model_dump())
    except PolicyError as exc:
        _policy_to_http(exc)
    return schemas.VMResponse.model_validate(vm)


# ─────────────────────────── ISO Management ───────────────────────────────

@router.get(
    "/isos",
    response_model=schemas.ISOListResponse,
    summary="Lister les ISOs disponibles",
)
def list_isos(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    items = vm_service.list_isos(db, current_user.id, current_user.role.value)
    return schemas.ISOListResponse(
        items=[schemas.ISOResponse.model_validate(i) for i in items],
        total=len(items),
    )


@router.post(
    "/isos/download",
    response_model=schemas.ISOResponse,
    status_code=202,
    summary="Lancer le téléchargement d'une ISO via URL (avec cache)",
)
def download_iso(
    body: schemas.ISODownloadRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    try:
        iso = vm_service.download_iso(db, current_user.id, body.model_dump())
    except PolicyError as exc:
        _policy_to_http(exc)
    return schemas.ISOResponse.model_validate(iso)


@router.get(
    "/isos/{iso_id}/status",
    response_model=schemas.ISOStatusResponse,
    summary="Statut du téléchargement d'une ISO (polling HTTP)",
)
def iso_download_status(
    iso_id: uuid.UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    try:
        result = vm_service.get_iso_status(db, iso_id, current_user.id, current_user.role.value)
    except PolicyError as exc:
        _policy_to_http(exc)
    return schemas.ISOStatusResponse(**result)


@router.websocket("/isos/{iso_id}/ws-status")
async def iso_ws_status(
    iso_id: uuid.UUID,
    websocket: WebSocket,
    db: Session = Depends(get_db),
):
    """
    WebSocket — suivi temps réel du téléchargement d'une ISO.

    Le client se connecte et reçoit des mises à jour toutes les 3 secondes
    jusqu'à ce que le statut soit terminal (VALIDATED, ERROR, PENDING_ANALYST).

    Protocole :
        → connexion établie
        ← JSON { iso_id, status, proxmox_task_status, progress_pct, ... }
        ... (répété jusqu'à status terminal)
        ← connexion fermée par le serveur
    """
    await websocket.accept()

    # Récupération de l'utilisateur depuis le token (query param)
    # Le frontend doit passer ?token=<jwt> dans l'URL WebSocket
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Token manquant")
        return

    from horizon.features.auth.service import decode_access_token
    from horizon.shared.models import User

    try:
        payload = decode_access_token(token)
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            await websocket.close(code=4003, reason="Utilisateur introuvable")
            return
    except Exception:
        await websocket.close(code=4003, reason="Token invalide")
        return

    TERMINAL = {"VALIDATED", "PENDING_ANALYST", "ERROR"}

    try:
        while True:
            try:
                result = vm_service.get_iso_status(
                    db, iso_id, user.id, user.role.value
                )
            except PolicyError as exc:
                await websocket.send_json({"error": exc.message})
                break

            await websocket.send_json(result)

            if result.get("status") in TERMINAL:
                break

            await asyncio.sleep(3)

    except WebSocketDisconnect:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# ─────────────────────────── Opérations communes ──────────────────────────

@router.get(
    "",
    response_model=schemas.VMListResponse,
    summary="Lister mes VMs",
)
def list_vms(current_user: CurrentUser, db: Session = Depends(get_db)):
    rows = vm_service.get_user_vms(db, current_user.id)
    return schemas.VMListResponse(
        items=[schemas.VMResponse.model_validate(r) for r in rows],
        total=len(rows),
    )


@router.get(
    "/{vm_id}",
    response_model=schemas.VMResponse,
    summary="Détail d'une VM",
)
def get_vm(vm_id: uuid.UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise PolicyError("VM", "VM introuvable.", 404)
    enforce_vm_ownership(vm.owner_id, current_user.id, current_user.role.value)
    return schemas.VMResponse.model_validate(vm)


@router.post(
    "/{vm_id}/stop",
    response_model=schemas.VMStopResponse,
    summary="Éteindre une VM (arrêt propre ACPI)",
)
def stop_vm(vm_id: uuid.UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        upid = vm_service.stop_vm(db, vm_id, current_user.id, current_user.role.value)
    except PolicyError as exc:
        _policy_to_http(exc)
    return schemas.VMStopResponse(message="Arrêt initié.", upid=upid)


@router.delete("/{vm_id}", status_code=204, summary="Supprimer définitivement une VM")
def delete_vm(vm_id: uuid.UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        vm_service.delete_vm(db, vm_id, current_user.id, current_user.role.value)
    except PolicyError as exc:
        _policy_to_http(exc)


@router.post(
    "/{vm_id}/extend",
    response_model=schemas.VMResponse,
    summary="Prolonger la session d'une VM",
)
def extend_vm(
    vm_id: uuid.UUID,
    body: schemas.VMExtendRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    try:
        vm = vm_service.extend_vm_lease(
            db, vm_id, current_user.id, current_user.role.value, body.additional_hours
        )
    except PolicyError as exc:
        _policy_to_http(exc)
    return schemas.VMResponse.model_validate(vm)


@router.get(
    "/{vm_id}/ssh-key",
    response_model=schemas.SSHKeyDownloadResponse,
    summary="Télécharger la clé SSH publique (une seule fois)",
)
def get_ssh_key(vm_id: uuid.UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise PolicyError("VM", "VM introuvable.", 404)
    enforce_vm_ownership(vm.owner_id, current_user.id, current_user.role.value)

    if not vm.ssh_public_key:
        raise PolicyError(
            "VM",
            "La clé SSH a déjà été téléchargée ou n'est pas disponible.",
            410,
        )

    key_data = vm.ssh_public_key
    log_action(db, current_user.id, AuditAction.FILE_DOWNLOADED, "vm", vm.id, metadata={"type": "ssh_key"})
    vm.ssh_public_key = None
    db.commit()

    return schemas.SSHKeyDownloadResponse(
        ssh_public_key=key_data,
        warning="Clé disponible une seule fois. Conservez-la en lieu sûr.",
    )
