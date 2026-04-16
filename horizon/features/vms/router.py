"""Routes /api/v1/vms."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from horizon.core.config import get_settings
from horizon.features.vms import schemas
from horizon.features.vms import service as vm_service
from horizon.infrastructure.database import get_db
from horizon.shared.dependencies import CurrentUser
from horizon.shared.models import AuditAction, VirtualMachine
from horizon.shared.audit_service import log_action
from horizon.shared.policies.enforcer import PolicyError, enforce_vm_ownership
router = APIRouter(prefix="/vms", tags=["Machines Virtuelles"])


@router.post(
    "",
    response_model=schemas.VMResponse,
    status_code=201,
    summary="Créer une VM",
)
def create_vm(
    body: schemas.VMCreateRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    vm = vm_service.create_vm(db, current_user.id, body.model_dump())
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


@router.get("/{vm_id}", response_model=schemas.VMResponse, summary="Détail d'une VM")
def get_vm(vm_id: uuid.UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise PolicyError("VM", "VM introuvable.", 404)
    enforce_vm_ownership(vm.owner_id, current_user.id, current_user.role.value)
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
def stop_vm(vm_id: uuid.UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    vm_service.stop_vm(db, vm_id, current_user.id, current_user.role.value)
    return schemas.VMStopMessageResponse(message="VM arrêtée.")


@router.delete("/{vm_id}", status_code=204, summary="Supprimer définitivement une VM")
def delete_vm(vm_id: uuid.UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    vm_service.delete_vm(db, vm_id, current_user.id, current_user.role.value)


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

@router.post("/{vm_id}/vnc", summary="Obtenir un accès console VNC à la VM")
def get_vm_vnc(
    vm_id: uuid.UUID, 
    current_user: CurrentUser, 
    db: Session = Depends(get_db)
):
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise PolicyError("VM", "VM introuvable.", 404)
    
    enforce_vm_ownership(vm.owner_id, current_user.id, current_user.role.value)
    
    from horizon.infrastructure.proxmox_client import ProxmoxClient
    from horizon.features.vms.service import _resolve_proxmox_node_name
    
    client = ProxmoxClient()
    if not client.enabled:
        raise PolicyError("PROXMOX", "Le service Proxmox est désactivé dans la configuration.", 503)
        
    px_node = _resolve_proxmox_node_name(db, vm.node)
    ticket_data = client.get_vnc_proxy(px_node, vm.proxmox_vmid)
    
    # On construit l'URL NoVNC pour le frontend
    # Format: https://<host>:8006/?console=kvm&novnc=1&node=<node>&vmid=<vmid>&ticket=<ticket>&password=<password>
    return {
        "url": f"https://{get_settings().PROXMOX_HOST}:8006/",
        "ticket": ticket_data["ticket"],
        "port": ticket_data["port"],
        "upid": ticket_data["upid"],
        "node": px_node,
        "vmid": vm.proxmox_vmid,
        "user": get_settings().PROXMOX_USER
    }


@router.post("/{vm_id}/terminal", summary="Obtenir un accès terminal xtermjs à la VM")
def get_vm_terminal(
    vm_id: uuid.UUID, 
    current_user: CurrentUser, 
    db: Session = Depends(get_db)
):
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise PolicyError("VM", "VM introuvable.", 404)
    
    enforce_vm_ownership(vm.owner_id, current_user.id, current_user.role.value)
    
    from horizon.infrastructure.proxmox_client import ProxmoxClient
    from horizon.features.vms.service import _resolve_proxmox_node_name
    
    client = ProxmoxClient()
    if not client.enabled:
        raise PolicyError("PROXMOX", "Le service Proxmox est désactivé.", 503)
        
    px_node = _resolve_proxmox_node_name(db, vm.node)
    ticket_data = client.get_xterm_proxy(px_node, vm.proxmox_vmid)
    
    return {
        "socket_url": f"wss://{get_settings().PROXMOX_HOST}:8006/api2/json/nodes/{px_node}/qemu/{vm.proxmox_vmid}/vncwebsocket",
        "ticket": ticket_data["ticket"],
        "port": ticket_data["port"],
        "node": px_node,
        "vmid": vm.proxmox_vmid
    }
