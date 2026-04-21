import uuid
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from horizon.core.config import get_settings
from horizon.features.vms import schemas
from horizon.features.vms import service as vm_service
from horizon.features.vms.service import _resolve_proxmox_node_name
from horizon.infrastructure.database import get_db
from horizon.shared.dependencies import CurrentUser
from horizon.shared.models import AuditAction, VirtualMachine, VMStatus
from horizon.shared.audit_service import log_action
from horizon.shared.policies.enforcer import PolicyError, enforce_vm_ownership

settings = get_settings()
router = APIRouter(prefix="/vms", tags=["Machines Virtuelles"])


@router.get("/cluster-status", summary="État rapide du cluster (tous les utilisateurs authentifiés)")
async def get_cluster_status(current_user: CurrentUser):
    """
    Retourne uniquement le statut online/offline du cluster et le nombre de nœuds,
    sans exposer les noms des nœuds ni la topologie de l'infrastructure.
    Utilise un appel direct à l'API Proxmox pour éviter tout état mis en cache.
    """
    from horizon.core.config import get_settings
    from horizon.infrastructure.proxmox_client import ProxmoxClient

    settings = get_settings()
    if not settings.PROXMOX_ENABLED:
        return {"online": False, "total_nodes": 0, "online_nodes": 0}
    try:
        client = ProxmoxClient()
        # Appel direct — lève une exception si Proxmox est inaccessible
        nodes = client.api.nodes.get()
        online_nodes = sum(1 for n in nodes if n.get("status") == "online")
        return {
            "online": online_nodes > 0,
            "total_nodes": len(nodes),
            "online_nodes": online_nodes,
        }
    except Exception:
        return {"online": False, "total_nodes": 0, "online_nodes": 0}


@router.get("/available-isos", summary="Lister les images ISO disponibles")
def list_available_isos(current_user: CurrentUser, db: Session = Depends(get_db)):
    from horizon.shared.models import ISOImage
    rows = db.query(ISOImage).filter(ISOImage.is_active == True).all()
    return {"items": rows}


@router.get("/quota", summary="Consulter mes quotas")
def get_my_quota(current_user: CurrentUser, db: Session = Depends(get_db)):
    from horizon.features.vms.quota_service import get_effective_quota, count_active_vms
    q = get_effective_quota(db, current_user.id)
    active_vms = count_active_vms(db, current_user.id)
    return {
        "max_vcpu_per_vm": q.max_vcpu_per_vm,
        "max_ram_gb_per_vm": q.max_ram_gb_per_vm,
        "max_storage_gb_per_vm": q.max_storage_gb_per_vm,
        "max_simultaneous_vms": q.max_simultaneous_vms,
        "max_session_duration_hours": q.max_session_duration_hours,
        "active_vms_count": active_vms,
        "remaining_vms": max(0, q.max_simultaneous_vms - active_vms)
    }


@router.post(
    "",
    response_model=schemas.VMResponse,
    status_code=201,
    summary="Créer une VM",
)
async def create_vm(
    body: schemas.VMCreateRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    vm = await vm_service.create_vm(db, current_user.id, body.model_dump())
    return vm


@router.get(
    "",
    response_model=schemas.VMListResponse,
    summary="Lister mes VMs",
)
def list_vms(current_user: CurrentUser, db: Session = Depends(get_db)):
    rows = vm_service.get_user_vms(db, current_user.id)
    return schemas.VMListResponse(
        items=[schemas.VMResponse.model_validate(r) for r in rows]
    )


@router.get("/{vm_id}/console")
async def get_vm_console(
    vm_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    vm = vm_service._get_vm_or_404(db, vm_id)
    enforce_vm_ownership(vm.owner_id, current_user.id, current_user.role.value)

    from horizon.infrastructure.proxmox_client import ProxmoxClient
    client = ProxmoxClient()
    if not client.enabled:
        raise HTTPException(status_code=503, detail="Service Proxmox indisponible")

    px_node = _resolve_proxmox_node_name(db, vm.node)
    try:
        vnc_data = await client.get_vnc_proxy(px_node, vm.proxmox_vmid)
        # On ajoute des infos pour que le frontend sache où se connecter
        vnc_data["host"] = settings.PROXMOX_HOST
        vnc_data["node"] = px_node
        vnc_data["vmid"] = vm.proxmox_vmid
        return vnc_data
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{vm_id}", response_model=schemas.VMResponse, summary="Détail d'une VM")
def get_vm(vm_id: uuid.UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise PolicyError("VM", "VM introuvable.", 404)
    enforce_vm_ownership(vm.owner_id, current_user.id, current_user.role.value)

    # Auto-refresh IP if missing and VM is active
    if vm.status == VMStatus.ACTIVE:
        from horizon.infrastructure.proxmox_client import ProxmoxClient
        try:
            client = ProxmoxClient()
            if client.enabled:
                px_node = _resolve_proxmox_node_name(db, vm.node)
                status = client.get_vm_current_status(px_node, vm.proxmox_vmid)
                
                # Attacher les stats dynamiques (non persistées en DB)
                vm.cpu_usage = round(status.get("cpu", 0) * 100, 1)
                mem_used = status.get("mem", 0)
                mem_max = status.get("maxmem", 1)
                vm.ram_usage = round((mem_used / mem_max) * 100, 1)
                
                # Refresh IP si manquante
                if not vm.ip_address:
                    ips = client.get_vm_ips(px_node, vm.proxmox_vmid)
                    if ips:
                        vm.ip_address = ips[0]
                        db.commit()
        except Exception:
            pass

    return vm


@router.patch(
    "/{vm_id}",
    response_model=schemas.VMResponse,
    summary="Modifier les ressources d'une VM",
)
def update_vm(
    vm_id: uuid.UUID,
    body: schemas.VMUpdateRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    return vm_service.update_vm(
        db,
        vm_id,
        current_user.id,
        current_user.role.value,
        body.model_dump(exclude_none=True),
    )


@router.post(
    "/{vm_id}/stop",
    response_model=schemas.VMStopMessageResponse,
    summary="Éteindre une VM",
)
async def stop_vm(vm_id: uuid.UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    await vm_service.stop_vm(db, vm_id, current_user.id, current_user.role.value)
    return schemas.VMStopMessageResponse(message="VM arrêtée.")


@router.post(
    "/{vm_id}/start",
    response_model=dict,
    summary="Démarrer une VM",
)
async def start_vm(vm_id: uuid.UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    await vm_service.start_vm(db, vm_id, current_user.id, current_user.role.value)
    return {"message": "VM démarrée."}


@router.delete("/{vm_id}", status_code=204, summary="Supprimer définitivement une VM")
async def delete_vm(vm_id: uuid.UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    await vm_service.delete_vm(db, vm_id, current_user.id, current_user.role.value)


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
    return vm_service.extend_vm_lease(
        db, vm_id, current_user.id, current_user.role.value, body.additional_hours
    )


@router.get(
    "/{vm_id}/ssh-key",
    response_model=schemas.SSHKeyDownloadResponse,
    summary="Télécharger la clé SSH (une seule fois)",
)
def get_ssh_key(vm_id: uuid.UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise PolicyError("VM", "VM introuvable.", 404)
    enforce_vm_ownership(vm.owner_id, current_user.id, current_user.role.value)

    if not vm.ssh_public_key:
        raise PolicyError(
            "POL-RESEAU-03",
            "La clé SSH a déjà été téléchargée ou n'est pas disponible.",
            410,
        )

    key_data = vm.ssh_public_key
    log_action(
        db,
        current_user.id,
        AuditAction.FILE_DOWNLOADED,
        "vm",
        vm.id,
        metadata={"type": "ssh_key"},
    )

    vm.ssh_public_key = None
    db.commit()

    return schemas.SSHKeyDownloadResponse(
        ssh_public_key=key_data,
        warning="Clé disponible une seule fois.",
    )


@router.post(
    "/{vm_id}/refresh",
    response_model=schemas.VMResponse,
    summary="Synchroniser l'état de la VM avec Proxmox (Force IP update)",
)
async def refresh_vm(vm_id: uuid.UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    return vm_service.refresh_vm_status(db, vm_id, current_user.id, current_user.role.value)
