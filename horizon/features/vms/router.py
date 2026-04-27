import uuid
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

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
    Retourne un état détaillé du cluster Proxmox accessible à tout utilisateur.
    Utilise ProxmoxClient.get_cluster_status() pour récupérer les stats globales (VMs, CPU, RAM).
    """
    from horizon.infrastructure.proxmox_client import ProxmoxClient

    settings = get_settings()
    if not settings.PROXMOX_ENABLED:
        return {
            "online": False,
            "total_nodes": 0,
            "online_nodes": 0,
            "active_vms": 0,
            "total_vms": 0,
            "total_cpus": 0,
            "total_memory": 0
        }
    try:
        client = ProxmoxClient()
        status = client.get_cluster_status()
        
        # On calcule online/offline à partir des nœuds retournés
        nodes = status.get("nodes", [])
        online_nodes = sum(1 for n in nodes if n.get("status") == "online")
        
        return {
            "online": online_nodes > 0,
            "total_nodes": len(nodes),
            "online_nodes": online_nodes,
            "active_vms": status.get("active_vms", 0),
            "total_vms": status.get("total_vms", 0),
            "total_cpus": status.get("total_cpus", 0),
            "total_memory": status.get("total_memory", 0)
        }
    except Exception:
        return {
            "online": False,
            "total_nodes": 0,
            "online_nodes": 0,
            "active_vms": 0,
            "total_vms": 0,
            "total_cpus": 0,
            "total_memory": 0
        }


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

@router.post("/proxmox/create-vm", summary="Créer une VM directement depuis un ISO (sans template)")
async def admin_create_proxmox_vm(
    body: schemas.ProxmoxCreateVMRequest, 
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    return await vm_service.create_vm_directly(db, current_user.id, body)


@router.get(
    "",
    response_model=schemas.VMListResponse,
    summary="Lister mes VMs",
)
def list_vms(current_user: CurrentUser, db: Session = Depends(get_db)):
    from datetime import datetime, timezone
    rows = vm_service.get_user_vms(db, current_user.id)
    items = []
    now = datetime.now(timezone.utc)
    
    for r in rows:
        # Local check for expiry to ensure immediate consistency in lists
        lease_end = r.lease_end
        if lease_end.tzinfo is None:
            lease_end = lease_end.replace(tzinfo=timezone.utc)
            
        if lease_end <= now and r.status != VMStatus.EXPIRED:
            r.status = VMStatus.EXPIRED
            r.stopped_at = now
            db.commit()
            logger.info(f"List: VM {r.id} detected as EXPIRED locally.")
            
        resp = schemas.VMResponse.model_validate(r)
        if r.iso_image:
            resp.os_name = r.iso_image.name
            resp.os_family = r.iso_image.os_family.value if hasattr(r.iso_image.os_family, 'value') else r.iso_image.os_family
        items.append(resp)
    return schemas.VMListResponse(items=items)


@router.get("/{vm_id}/console")
async def get_vm_console(
    vm_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    vm = vm_service._get_vm_or_404(db, vm_id)
    enforce_vm_ownership(vm.owner_id, current_user.id, current_user.role.value)
    vm_service.enforce_vm_active_lease(vm)

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


@router.websocket("/vnc/{vm_id}")
async def vnc_proxy_websocket(
    websocket: WebSocket,
    vm_id: str,
    port: str,
    ticket: str,
    db: Session = Depends(get_db),
):
    """
    WebSocket proxy for VNC console.
    Forwards the browser connection to the Proxmox VNC WebSocket endpoint.
    """
    # noVNC requests the 'binary' subprotocol — we must acknowledge it
    await websocket.accept(subprotocol="binary")

    try:
        # 1. Look up VM in the database
        from horizon.infrastructure.vnc_proxy import proxy_vnc
        vm_uuid = uuid.UUID(vm_id)
        vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_uuid).first()
        if not vm:
            logger.error(f"VNC: VM {vm_id} not found")
            await websocket.close(code=1008, reason="VM not found")
            return
        
        # 1b. Expiry check
        try:
            vm_service.enforce_vm_active_lease(vm)
        except Exception as e:
            await websocket.close(code=1008, reason=str(e))
            return

        # 2. Resolve the Proxmox node name
        _settings = get_settings()
        try:
            px_node = _resolve_proxmox_node_name(db, vm.node)
        except Exception as e:
            logger.error(f"VNC: node resolution failed for VM {vm_id}: {e}")
            px_node = _settings.PROXMOX_NODE or "pve1"

        logger.info(f"VNC proxy: vmid={vm.proxmox_vmid} node={px_node} port={port}")

        # 3. Start the proxy (ticket arrives URL-decoded from FastAPI query params)
        await proxy_vnc(
            websocket=websocket,
            proxmox_host=_settings.PROXMOX_HOST,
            node=px_node,
            vmid=vm.proxmox_vmid,
            port=port,
            ticket=ticket,
            root_user=_settings.PROXMOX_ROOT_USER,
            root_password=_settings.PROXMOX_ROOT_PASSWORD,
            verify_ssl=_settings.PROXMOX_VERIFY_SSL,
        )

    except Exception as e:
        logger.error(f"VNC WebSocket Error for {vm_id}: {e}", exc_info=True)
        try:
            await websocket.close(code=1011)
        except Exception:
            pass


@router.websocket("/ssh/{vm_id}")
async def ssh_proxy_websocket(
    websocket: WebSocket,
    vm_id: str,
    token: str = None,
    db: Session = Depends(get_db),
):
    """
    WebSocket proxy for SSH terminal.
    """
    await websocket.accept()

    try:
        # 1. Auth check
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            return
        
        from horizon.features.auth.service import get_user_from_token
        try:
            current_user = get_user_from_token(db, token)
        except Exception:
            await websocket.close(code=1008, reason="Invalid token")
            return

        # 2. Look up VM
        from horizon.infrastructure.ssh_proxy import proxy_ssh
        vm_uuid = uuid.UUID(vm_id)
        vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_uuid).first()
        if not vm:
            await websocket.close(code=1008, reason="VM not found")
            return
        
        # 3. Ownership check
        try:
            enforce_vm_ownership(vm.owner_id, current_user.id, current_user.role.value)
            vm_service.enforce_vm_active_lease(vm)
        except Exception as e:
            await websocket.close(code=1008, reason=str(e))
            return

        if not vm.ip_address:
            # Try to refresh IP
            from horizon.infrastructure.proxmox_client import ProxmoxClient
            client = ProxmoxClient()
            if client.enabled:
                px_node = _resolve_proxmox_node_name(db, vm.node)
                ips = client.get_vm_ips(px_node, vm.proxmox_vmid)
                if ips:
                    vm.ip_address = ips[0]
                    db.commit()
            
            if not vm.ip_address:
                await websocket.close(code=1011, reason="VM has no IP address")
                return

        # 4. Determine credentials
        username = 'user' if vm.os_family != 'WINDOWS' else 'Administrator'
        # If the VM has an os_name that implies a different user, we could refine this.
        
        # Check if we have a stored private key (for download)
        pkey = vm.ssh_public_key if vm.ssh_public_key and "-----BEGIN" in vm.ssh_public_key else None
        
        logger.info(f"SSH Terminal: Connecting to {vm.ip_address} for user {current_user.email}")
        
        await proxy_ssh(
            websocket=websocket,
            host=vm.ip_address,
            username=username,
            private_key_str=pkey
        )

    except Exception as e:
        logger.error(f"SSH WebSocket Error for {vm_id}: {e}", exc_info=True)
        try:
            await websocket.close(code=1011)
        except Exception:
            pass


@router.get("/{vm_id}", response_model=schemas.VMResponse, summary="Détail d'une VM")
def get_vm(vm_id: uuid.UUID, current_user: CurrentUser, db: Session = Depends(get_db)):
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise PolicyError("VM", "VM introuvable.", 404)
    enforce_vm_ownership(vm.owner_id, current_user.id, current_user.role.value)

    # Synchroniser l'état avec Proxmox (IP, Status, Stats)
    vm = vm_service.refresh_vm_status(db, vm_id, current_user.id, current_user.role.value)

    # Attacher les stats dynamiques (non persistées en DB)
    if vm.status == VMStatus.ACTIVE:
        from horizon.infrastructure.proxmox_client import ProxmoxClient
        try:
            client = ProxmoxClient()
            if client.enabled:
                px_node = _resolve_proxmox_node_name(db, vm.node)
                status = client.get_vm_current_status(px_node, vm.proxmox_vmid)
                
                vm.cpu_usage = round(status.get("cpu", 0) * 100, 1)
                mem_used = status.get("mem", 0)
                mem_max = status.get("maxmem", 1)
                vm.ram_usage = round((mem_used / mem_max) * 100, 1)
        except Exception:
            pass

    resp = schemas.VMResponse.model_validate(vm)
    if vm.iso_image:
        resp.os_name = vm.iso_image.name
        resp.os_family = vm.iso_image.os_family.value if hasattr(vm.iso_image.os_family, 'value') else vm.iso_image.os_family
    
    return resp


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
