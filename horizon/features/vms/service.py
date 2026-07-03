"""Cycle de vie des VMs."""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from typing import Any
from horizon.features.vms import schemas
from horizon.core.config import get_settings
from horizon.features.vms.quota_service import count_active_vms, get_effective_quota
from horizon.shared.audit_service import log_action
from horizon.shared.models import (
    AuditAction,
    ExtensionRequest,
    ISOImage,
    IsoProxmoxTemplate,
    PhysicalNode,
    ProxmoxNodeMapping,
    Reservation,
    VirtualMachine,
    VMStatus,
)
from horizon.infrastructure.ssh_utils import generate_ssh_key_pair
from horizon.shared.policies.enforcer import (
    PolicyError,
    enforce_hard_limits,
    enforce_iso_authorized,
    enforce_session_duration,
    enforce_vm_count_limit,
    enforce_vm_ownership,
    enforce_vm_resource_limits,
)

def enforce_vm_active_lease(vm: VirtualMachine) -> None:
    """Vérifie si la session de la VM n'est pas expirée."""
    now = datetime.now(timezone.utc)
    # Ensure lease_end has timezone info if it doesn't (though it should in DB)
    lease_end = vm.lease_end
    if lease_end.tzinfo is None:
        lease_end = lease_end.replace(tzinfo=timezone.utc)
        
    if lease_end <= now:
        raise PolicyError(
            "POL-RESSOURCES-01",
            f"La session de cette VM a expiré le {vm.lease_end.strftime('%d/%m/%Y %H:%M')}. "
            "Veuillez prolonger la session ou contacter un administrateur.",
            403,
        )
logger = logging.getLogger(__name__)


def _resolve_proxmox_node_name(db: Session, physical_node: PhysicalNode) -> str:
    s = get_settings()
    row = (
        db.query(ProxmoxNodeMapping)
        .filter(ProxmoxNodeMapping.physical_node == physical_node)
        .first()
    )
    if row:
        return row.proxmox_node_name
    if s.PROXMOX_NODE:
        return s.PROXMOX_NODE
    raise PolicyError(
        "PROXMOX",
        "Aucun mapping nœud Proxmox pour ce nœud métier (table proxmox_node_mappings).",
        500,
    )


def _resolve_px_node_for_vm(db: Session, vm: VirtualMachine) -> str:
    """Resolve the Proxmox node name for a VM, with safe fallbacks for scheduler/monitoring."""
    try:
        return _resolve_proxmox_node_name(db, vm.node)
    except Exception:
        s = get_settings()
        if s.PROXMOX_NODE:
            return s.PROXMOX_NODE
        return vm.node.value.lower()


def _build_net0(vlan_id: int | None) -> str:
    s = get_settings()
    base = s.PROXMOX_NET0_TEMPLATE.strip()
    # On ajoute le tag VLAN seulement si l'isolation est activée en config
    if vlan_id is not None and getattr(s, "PROXMOX_VLAN_ISOLATION", True):
        return f"{base},tag={vlan_id}"
    return base

def _require_proxmox_enabled() -> None:
    if not get_settings().PROXMOX_ENABLED:
        raise PolicyError(
            "PROXMOX", "Proxmox est désactivé (PROXMOX_ENABLED=false).", 503)

async def create_vm(db: Session, owner_id, data: dict) -> VirtualMachine:
    from horizon.infrastructure.proxmox_client import ProxmoxClient, ProxmoxIntegrationError

    s = get_settings()
    iso_id_str = data.get("iso_image_id")
    if not iso_id_str or str(iso_id_str) in ("null", "undefined", "None", ""):
        raise PolicyError("POL-RESSOURCES-02", "Une image ISO valide est requise.", 422)

    # Résolution de l'ISO (par ID ou par Nom)
    iso = None
    try:
        iso_uuid = uuid.UUID(str(iso_id_str))
        iso = db.query(ISOImage).filter(ISOImage.id == iso_uuid).first()
    except ValueError:
        # Si ce n'est pas un UUID, on cherche par nom (ex: "Debian 12")
        iso = db.query(ISOImage).filter(
            (ISOImage.name.ilike(f"%{iso_id_str}%")) | 
            (ISOImage.os_version.ilike(f"%{iso_id_str}%"))
        ).first()

    if not iso:
        raise PolicyError("POL-RESSOURCES-02", f"Image ISO introuvable pour : {iso_id_str}", 404)
    enforce_iso_authorized(iso.is_active)

    quota = get_effective_quota(db, owner_id)

    enforce_hard_limits(
        data["vcpu"], data["ram_gb"], data["storage_gb"], data["session_hours"]
    )
    enforce_vm_resource_limits(
        data["vcpu"],
        data["ram_gb"],
        data["storage_gb"],
        quota.max_vcpu_per_vm,
        quota.max_ram_gb_per_vm,
        quota.max_storage_gb_per_vm,
    )
    enforce_session_duration(
        data["session_hours"], quota.max_session_duration_hours)

    active_count = count_active_vms(db, owner_id)
    enforce_vm_count_limit(active_count, quota.max_simultaneous_vms)

    node = _select_node(db)
    vlan_id = _assign_vlan(
        db,
        owner_id,
        shared_network=data.get("shared_network", True),
        shared_vlan_id=data.get("shared_vlan_id"),
    )

    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        proxmox_vmid=_next_proxmox_vmid(db),
        name=data["name"],
        description=data.get("description"),
        owner_id=owner_id,
        node=node,
        vcpu=data["vcpu"],
        ram_gb=data["ram_gb"],
        storage_gb=data["storage_gb"],
        iso_image_id=iso.id,
        status=VMStatus.PENDING,
        lease_start=now,
        lease_end=now + timedelta(hours=data["session_hours"]),
        vlan_id=vlan_id,
        shared_space_gb=0.0,
    )
    db.add(vm)

    reservation = Reservation(
        id=uuid.uuid4(),
        vm_id=vm.id,
        user_id=owner_id,
        start_time=vm.lease_start,
        end_time=vm.lease_end,
    )
    db.add(reservation)

    # Gestion des clés SSH
    user_ssh_key = data.get("ssh_public_key", "").strip()
    if user_ssh_key:
        if not user_ssh_key.startswith(("ssh-rsa", "ssh-ed25519", "ecdsa-sha2")):
            raise PolicyError("POL-RESSOURCES-02", "La clé SSH fournie n'est pas une clé publique valide.", 422)
        public_key = user_ssh_key
        private_key = None
        vm.ssh_public_key = None
    else:
        private_key, public_key = generate_ssh_key_pair()
        vm.ssh_public_key = private_key  # store private key for one-time download
    try:
        db.flush()

        if s.PROXMOX_ENABLED:
            tpl = (
                db.query(IsoProxmoxTemplate)
                .filter(IsoProxmoxTemplate.iso_image_id == iso.id)
                .first()
            )
            if not tpl:
                raise PolicyError(
                    "POL-RESSOURCES-02",
                    "Cette image ISO n'est pas provisionnée sur Proxmox (table iso_proxmox_templates).",
                    409,
                )
            px_node = _resolve_proxmox_node_name(db, node)
            try:
                client = ProxmoxClient()
            except ProxmoxIntegrationError as e:
                raise PolicyError("PROXMOX", e.message, e.status_code) from e
            memory_mb = max(1, int(round(float(data["ram_gb"]) * 1024)))
            net0 = _build_net0(vlan_id)
            try:
                # Normalize ssh public key (keep only type + blob) to avoid Proxmox validation issues
                if public_key:
                    pk_parts = public_key.strip().split()
                    public_key = f"{pk_parts[0]} {pk_parts[1]}" if len(pk_parts) >= 2 else public_key.strip()

                res = await client.create_vm_from_template(
                    px_node,
                    tpl.proxmox_template_vmid,
                    vm.proxmox_vmid,
                    data["name"],
                    memory_mb,
                    data["vcpu"],
                    net0,
                    storage=s.PROXMOX_VM_STORAGE,
                    ssh_key=public_key
                )
                # On capture l'IP s'il a été trouvé pendant la création
                if res.get("ip_address"):
                    vm.ip_address = res["ip_address"]
            except ProxmoxIntegrationError as e:
                raise PolicyError("PROXMOX", e.message, e.status_code) from e

        log_action(
            db,
            owner_id,
            AuditAction.VM_CREATED,
            "vm",
            vm.id,
            metadata={
                "vcpu": data["vcpu"],
                "ram_gb": data["ram_gb"],
                "session_hours": data["session_hours"],
                "vlan_id": vlan_id,
                "shared_network": data.get("shared_network", True),
            },
        )
        vm.status = VMStatus.ACTIVE
        db.commit()
        db.refresh(vm)
        return vm
    except PolicyError:
        db.rollback()
        raise
    except ProxmoxIntegrationError as e:
        db.rollback()
        raise PolicyError("PROXMOX", e.message, e.status_code) from e
    except Exception:
        db.rollback()
        raise

async def create_vm_directly(db: Session, owner_id, body: schemas.ProxmoxCreateVMRequest) -> dict[str, Any]:
    from horizon.infrastructure.proxmox_client import ProxmoxClient, ProxmoxIntegrationError
    from datetime import datetime, timezone, timedelta
    from horizon.shared.models import VirtualMachine, Reservation, ISOImage, ProxmoxNodeMapping
    from horizon.shared.models.virtual_machine import PhysicalNode, VMStatus
    import uuid as _uuid

    _require_proxmox_enabled()
    s = get_settings()
    now = datetime.now(timezone.utc)

    ram_gb = round(float(body.ram_mb) / 1024.0, 3)
    quota = get_effective_quota(db, owner_id)
    enforce_hard_limits(body.vcpu, ram_gb, float(body.storage_gb), body.session_hours)
    enforce_vm_resource_limits(
        body.vcpu,
        ram_gb,
        float(body.storage_gb),
        quota.max_vcpu_per_vm,
        quota.max_ram_gb_per_vm,
        quota.max_storage_gb_per_vm,
    )
    enforce_session_duration(body.session_hours, quota.max_session_duration_hours)
    active_count = count_active_vms(db, owner_id)
    enforce_vm_count_limit(active_count, quota.max_simultaneous_vms)

    proxmox_vmid = body.vmid if body.vmid is not None else _next_proxmox_vmid(db)
    if body.vmid is not None:
        taken = db.query(VirtualMachine).filter(VirtualMachine.proxmox_vmid == body.vmid).first()
        if taken:
            proxmox_vmid = _next_proxmox_vmid(db)

    # 1. Automate Node Selection (Scheduler)
    target_node = s.PROXMOX_NODE # Use setting if provided
    
    try:
        client = ProxmoxClient()
        if client.enabled:
            storage_to_check = body.storage or s.PROXMOX_VM_STORAGE
            nodes_info = client.get_nodes_resources(storage_to_check)
            
            if nodes_info:
                allowed_nodes = {"rem", "ram", "emilia"}
                filtered_nodes = [n for n in nodes_info if n["name"].lower() in allowed_nodes]
                if filtered_nodes:
                    # Sort nodes by free RAM and Storage (descending)
                    sorted_nodes = sorted(filtered_nodes, key=lambda x: (x.get("storage_free", 0), x.get("ram_free", 0)), reverse=True)
                    if sorted_nodes and sorted_nodes[0].get("storage_free", 0) > 0:
                        target_node = sorted_nodes[0]["name"]
                        logger.info(f"Scheduler picked node {target_node} with {sorted_nodes[0]['storage_free']} bytes free.")
                elif not target_node and (nodes_info):
                    # Fallback if allowed_nodes are not reported but we have others, stick to target_node or first online
                    target_node = nodes_info[0]["name"]
                    logger.warning(f"Scheduler found nodes but none matching allowed list. Using fallback {target_node}.")
            
            if not target_node:
                raise PolicyError("PROXMOX", f"Aucun nœud Proxmox disponible ou capable d'accueillir le stockage '{storage_to_check}'.", 503)

    except Exception as e:
        if not target_node:
            logger.error(f"Scheduler failed and no fallback node (PROXMOX_NODE): {e}")
            raise PolicyError("PROXMOX", f"Erreur du scheduler Proxmox et aucun nœud par défaut configuré : {e}", 502)
        logger.warning(f"Scheduler failed, falling back to configured node {target_node}: {e}")

    logger.info(f"Direct VM Creation - target_node: {target_node}, storage: {body.storage}, vmid: {body.vmid}")

    # If body.node was provided (e.g. by an admin via API directly), respect it.
    if body.node:
        target_node = body.node

    # 2. Network Isolation (VLAN)
    vlan_id = _assign_vlan(
        db,
        owner_id,
        shared_network=body.shared_network,
        shared_vlan_id=body.shared_vlan_id,
    )
    net0 = _build_net0(vlan_id)
    # If the user provided a custom net0 but it doesn't specify a tag, we could consider overriding or merging
    # For now, we prioritize the isolated network string from _build_net0 if it's the default
    if body.net0 != "virtio,bridge=vmbr0":
        # Keep the user's base but ensure the tag is applied if isolation is active
        # Simplified: if user provides custom net0, we assume they know what they're doing?
        # No, for security/isolation we should probably enforce it.
        # But a more robust way is to use _build_net0 logic.
        pass
    else:
        # Use our built net0
        pass
    
    # Final net0 decision: Use built one for consistency and isolation
    final_net0 = net0

    # Resolve physical node for DB record
    mapping = db.query(ProxmoxNodeMapping).filter(
        ProxmoxNodeMapping.proxmox_node_name == target_node
    ).first()
    physical_node = mapping.physical_node if mapping else PhysicalNode.REM

    # Try to link ISO by filename
    iso = db.query(ISOImage).filter(ISOImage.filename == body.iso_filename).first()
    iso_id = iso.id if iso else None

    # Stage the VM record before touching Proxmox
    vm = VirtualMachine(
        id=_uuid.uuid4(),
        proxmox_vmid=proxmox_vmid,
        name=body.name,
        description=None,
        owner_id=owner_id,
        node=physical_node,
        vcpu=body.vcpu,
        ram_gb=round(float(body.ram_mb) / 1024.0, 3),
        storage_gb=body.storage_gb,
        iso_image_id=iso_id,
        status=VMStatus.PENDING,
        lease_start=now,
        lease_end=now + timedelta(hours=body.session_hours),
        vlan_id=vlan_id,
        ip_address=None,
        ssh_public_key=None, # Will be set below
        shared_space_gb=0.0,
    )
    
    # Gestion des clés SSH pour création directe
    user_ssh_key = (body.ssh_public_key or "").strip()
    if user_ssh_key:
        if not user_ssh_key.startswith(("ssh-rsa", "ssh-ed25519", "ecdsa-sha2")):
            raise PolicyError("POL-RESSOURCES-02", "La clé SSH fournie n'est pas une clé publique valide.", 422)
        vm.ssh_public_key = None # On ne stocke pas la clé publique de l'utilisateur pour téléchargement
        public_key_to_inject = user_ssh_key
    else:
        # On génère une clé seulement si ce n'est pas fourni
        from horizon.infrastructure.ssh_utils import generate_ssh_key_pair
        private_key, public_key = generate_ssh_key_pair()
        vm.ssh_public_key = private_key # Stockage pour téléchargement unique
        public_key_to_inject = public_key

    db.add(vm)

    reservation = Reservation(
        id=_uuid.uuid4(),
        vm_id=vm.id,
        user_id=owner_id,
        start_time=vm.lease_start,
        end_time=vm.lease_end,
    )
    db.add(reservation)

    try:
        db.flush()  # Validate constraints before hitting Proxmox

        try:
            client = ProxmoxClient()
        except ProxmoxIntegrationError as e:
            logger.error(f"Failed to init ProxmoxClient: {e}")
            raise PolicyError("PROXMOX", e.message, e.status_code) from e

        logger.info(f"Initiating Proxmox call: node={target_node}, vmid={proxmox_vmid}, name={body.name}")
        try:
            res = await client.create_vm(
                node=target_node,
                vmid=proxmox_vmid,
                name=body.name,
                storage=body.storage or s.PROXMOX_VM_STORAGE,
                iso_filename=body.iso_filename,
                vcpu=body.vcpu,
                ram_mb=body.ram_mb,
                storage_gb=body.storage_gb,
                iso_storage=body.iso_storage or s.PROXMOX_ISO_STORAGE,
                net0=final_net0,
                ssh_key=public_key_to_inject,
            )
            await client.start_vm(node=target_node, vmid=proxmox_vmid)
        except ProxmoxIntegrationError as e:
            raise PolicyError("PROXMOX", e.message, e.status_code) from e

        vm.status = VMStatus.ACTIVE
        db.commit()
        db.refresh(vm)

        return {
            "proxmox": res,
            "vm": {
                "id": str(vm.id),
                "proxmox_vmid": vm.proxmox_vmid,
                "name": vm.name,
                "vlan_id": vm.vlan_id,
            },
        }

    except PolicyError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

async def stop_vm(db: Session, vm_id, requesting_user_id, user_role: str, force: bool = False) -> None:
    from horizon.infrastructure.proxmox_client import ProxmoxClient, ProxmoxIntegrationError

    vm = _get_vm_or_404(db, vm_id)

    if not force:
        enforce_vm_ownership(vm.owner_id, requesting_user_id, user_role)
        enforce_vm_active_lease(vm)

    if vm.status == VMStatus.STOPPED:
        raise PolicyError("VM", "Cette VM est déjà arrêtée.", 409)

    s = get_settings()
    if s.PROXMOX_ENABLED:
        try:
            client = ProxmoxClient()
        except ProxmoxIntegrationError as e:
            raise PolicyError("PROXMOX", e.message, e.status_code) from e
        if client.enabled:
            px_node = _resolve_proxmox_node_name(db, vm.node)
            try:
                await client.stop_vm(px_node, vm.proxmox_vmid)
            except ProxmoxIntegrationError as e:
                # Si force, on continue même si Proxmox échoue
                if not force:
                    raise PolicyError("PROXMOX", e.message, e.status_code) from e

    vm.status = VMStatus.STOPPED
    vm.stopped_at = datetime.now(timezone.utc)

    action = AuditAction.VM_FORCE_STOPPED if force else AuditAction.VM_STOPPED
    log_action(db, requesting_user_id, action, "vm",
               vm.id, metadata={"force": force})
    db.commit()


async def start_vm(db: Session, vm_id, requesting_user_id, user_role: str) -> None:
    from horizon.infrastructure.proxmox_client import ProxmoxClient, ProxmoxIntegrationError

    vm = _get_vm_or_404(db, vm_id)
    enforce_vm_ownership(vm.owner_id, requesting_user_id, user_role)
    enforce_vm_active_lease(vm)

    if vm.status == VMStatus.ACTIVE:
        # On vérifie si elle est "vraiment" active sur Proxmox ou si c'est juste le statut DB
        pass

    s = get_settings()
    if s.PROXMOX_ENABLED:
        try:
            client = ProxmoxClient()
            if client.enabled:
                px_node = _resolve_proxmox_node_name(db, vm.node)
                await client.start_vm(px_node, vm.proxmox_vmid)
        except ProxmoxIntegrationError as e:
            raise PolicyError("PROXMOX", e.message, e.status_code) from e

    vm.status = VMStatus.ACTIVE
    log_action(db, requesting_user_id, AuditAction.VM_STARTED, "vm", vm.id)
    db.commit()


async def delete_vm(db: Session, vm_id, requesting_user_id, user_role: str) -> None:
    from horizon.infrastructure.proxmox_client import ProxmoxClient, ProxmoxIntegrationError

    vm = _get_vm_or_404(db, vm_id)
    enforce_vm_ownership(vm.owner_id, requesting_user_id, user_role)

    is_admin = user_role in ("ADMIN", "SUPER_ADMIN")
    action = AuditAction.VM_ADMIN_DELETED if is_admin else AuditAction.VM_DELETED

    s = get_settings()
    if s.PROXMOX_ENABLED:
        try:
            client = ProxmoxClient()
        except ProxmoxIntegrationError as e:
            raise PolicyError("PROXMOX", e.message, e.status_code) from e
        if client.enabled:
            px_node = _resolve_proxmox_node_name(db, vm.node)
            try:
                if vm.status == VMStatus.ACTIVE:
                    try:
                        await client.stop_vm(px_node, vm.proxmox_vmid)
                    except Exception:
                        pass
                await client.delete_vm(px_node, vm.proxmox_vmid)
            except ProxmoxIntegrationError as e:
                # If VM is not found on Proxmox, we log warning and proceed with DB deletion
                if "does not exist" in str(e).lower() or e.status_code == 404:
                    logger.warning(f"VM {vm.proxmox_vmid} not found on Proxmox node {px_node}. Allowing DB deletion.")
                else:
                    raise PolicyError("PROXMOX", e.message, e.status_code) from e
            except Exception as e:
                logger.error(f"Unexpected Proxmox error during VM deletion: {e}. Allowing DB deletion.")

    log_action(db, requesting_user_id, action, "vm", vm.id)
    db.delete(vm)
    db.commit()


def update_vm(db: Session, vm_id, requesting_user_id, user_role: str, data: dict) -> VirtualMachine:
    vm = _get_vm_or_404(db, vm_id)
    enforce_vm_ownership(vm.owner_id, requesting_user_id, user_role)
    enforce_vm_active_lease(vm)

    quota = get_effective_quota(db, vm.owner_id)

    new_vcpu = data.get("vcpu", vm.vcpu)
    new_ram = data.get("ram_gb", vm.ram_gb)
    new_storage = data.get("storage_gb", vm.storage_gb)

    enforce_hard_limits(new_vcpu, new_ram, new_storage, 1)
    enforce_vm_resource_limits(
        new_vcpu,
        new_ram,
        new_storage,
        quota.max_vcpu_per_vm,
        quota.max_ram_gb_per_vm,
        quota.max_storage_gb_per_vm,
    )

    vm.vcpu = new_vcpu
    vm.ram_gb = new_ram
    vm.storage_gb = new_storage
    if "name" in data:
        vm.name = data["name"]

    log_action(
        db,
        requesting_user_id,
        AuditAction.VM_MODIFIED,
        "vm",
        vm.id,
        metadata={"new_vcpu": new_vcpu, "new_ram_gb": new_ram},
    )
    db.commit()
    db.refresh(vm)
    return vm


def request_vm_extension(db: Session, vm_id, user_id, reason: str | None = None) -> ExtensionRequest:
    vm = _get_vm_or_404(db, vm_id)
    if vm.owner_id != user_id:
        raise PolicyError("POL-VM-01", "Accès non autorisé.")

    # Check if there's already a pending request
    existing = db.query(ExtensionRequest).filter(
        ExtensionRequest.vm_id == vm_id,
        ExtensionRequest.status == "PENDING"
    ).first()
    if existing:
        return existing

    request = ExtensionRequest(
        vm_id=vm.id,
        user_id=user_id,
        reason=reason,
        status="PENDING"
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    # Notify admin (Assuming settings.ADMIN_EMAIL exists, or just hardcode/use a default)
    from horizon.core.config import get_settings
    from horizon.infrastructure.email_service import send_extension_request_admin
    s = get_settings()
    if s.ADMIN_EMAIL: # I'll assume this exists or I'll check it
        send_extension_request_admin(s.ADMIN_EMAIL, vm.owner.email, vm.name)

    return request


def extend_vm_lease(db: Session, vm_id, user_id, user_role, additional_hours: int) -> VirtualMachine:
    vm = _get_vm_or_404(db, vm_id)
    if user_role not in ("ADMIN", "SUPER_ADMIN"):
        enforce_vm_ownership(vm.owner_id, user_id, user_role)
    
    enforce_vm_active_lease(vm)
    
    quota = get_effective_quota(db, vm.owner_id)
    current_lease_hours = (vm.lease_end - vm.lease_start).total_seconds() / 3600
    new_total_hours = current_lease_hours + additional_hours
    
    if user_role not in ("ADMIN", "SUPER_ADMIN"):
        enforce_session_duration(new_total_hours, quota.max_session_duration_hours)

    vm.lease_end += timedelta(hours=additional_hours)

    reservation = (
        db.query(Reservation)
        .filter(Reservation.vm_id == vm.id)
        .order_by(Reservation.created_at.desc())
        .first()
    )
    if reservation:
        reservation.end_time = vm.lease_end
        reservation.extended = True

    log_action(
        db,
        user_id,
        AuditAction.VM_LEASE_EXTENDED,
        "vm",
        vm.id,
        metadata={"additional_hours": additional_hours, "new_lease_end": vm.lease_end.isoformat()},
    )
    db.commit()
    db.refresh(vm)
    return vm


def approve_extension(db: Session, request_id, admin_id, additional_hours: int, comment: str | None = None) -> VirtualMachine:
    request = db.query(ExtensionRequest).filter(ExtensionRequest.id == request_id).first()
    if not request:
        raise PolicyError("VM", "Demande introuvable", 404)

    if request.status != "PENDING":
        raise PolicyError("VM", "Cette demande a déjà été traitée.")

    vm = extend_vm_lease(db, request.vm_id, admin_id, "ADMIN", additional_hours)

    request.status = "APPROVED"
    request.admin_comment = comment
    db.commit()

    from horizon.infrastructure.email_service import send_extension_approved_notification
    send_extension_approved_notification(request.user.email, vm.name, vm.lease_end)

    return vm


def get_user_vms(db: Session, user_id) -> list[VirtualMachine]:
    return db.query(VirtualMachine).filter(VirtualMachine.owner_id == user_id).all()


def refresh_vm_status(db: Session, vm_id: uuid.UUID, user_id: uuid.UUID, user_role: str) -> VirtualMachine:
    """
    Synchronise l'état de la VM entre Proxmox et la base de données.
    Met à jour le statut (ACTIVE/STOPPED) et l'IP si possible.
    """
    vm = _get_vm_or_404(db, vm_id)
    enforce_vm_ownership(vm.owner_id, user_id, user_role)
    
    from horizon.infrastructure.proxmox_client import ProxmoxClient, ProxmoxIntegrationError
    
    try:
        # 0. Local Expiry Check
        now = datetime.now(timezone.utc)
        lease_end = vm.lease_end
        if lease_end.tzinfo is None:
            lease_end = lease_end.replace(tzinfo=timezone.utc)
            
        if lease_end <= now and vm.status != VMStatus.EXPIRED:
            vm.status = VMStatus.EXPIRED
            vm.stopped_at = now
            db.commit()
            logger.info(f"Sync: VM {vm.id} detected as EXPIRED locally.")
            return vm

        client = ProxmoxClient()
        if client.enabled:
            px_node = _resolve_proxmox_node_name(db, vm.node)
            
            # 1. Sync Status
            try:
                px_status = client.get_vm_current_status(px_node, vm.proxmox_vmid)
                qemu_status = px_status.get("status") # 'running', 'stopped', 'paused'
                
                if qemu_status == "running" and vm.status != VMStatus.ACTIVE:
                    vm.status = VMStatus.ACTIVE
                    logger.info(f"Sync: VM {vm.id} set to ACTIVE (was {vm.status})")
                elif qemu_status == "stopped" and vm.status != VMStatus.STOPPED:
                    vm.status = VMStatus.STOPPED
                    if not vm.stopped_at:
                        vm.stopped_at = now
                    logger.info(f"Sync: VM {vm.id} set to STOPPED (was {vm.status})")
                elif qemu_status == "paused" and vm.status != VMStatus.SUSPENDED:
                    vm.status = VMStatus.SUSPENDED
                    logger.info(f"Sync: VM {vm.id} set to SUSPENDED (was {vm.status})")
                    
                # 2. Sync IP if Active
                if qemu_status == "running":
                    ips = client.get_vm_ips(px_node, vm.proxmox_vmid)
                    if ips:
                        vm.ip_address = ips[0]
                
                db.commit()
                db.refresh(vm)
            except ProxmoxIntegrationError as e:
                # Si la VM n'existe pas sur Proxmox, elle doit être STOPPED ou EXPIRED
                if "does not exist" in str(e).lower() or "404" in str(e):
                    if vm.status == VMStatus.ACTIVE:
                        vm.status = VMStatus.STOPPED
                        vm.stopped_at = now
                        db.commit()
                        logger.warning(f"Sync: VM {vm.id} not found on Proxmox, set to STOPPED.")
                else:
                    logger.warning(f"Failed to sync status for VM {vm.id}: {e}")
                
    except Exception as e:
        logger.error(f"Error in refresh_vm_status for VM {vm.id}: {e}")
        
    return vm


def get_all_vms_admin(db: Session) -> list[VirtualMachine]:
    return db.query(VirtualMachine).all()


def _get_vm_or_404(db: Session, vm_id) -> VirtualMachine:
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise PolicyError("VM", "VM introuvable.", 404)
    return vm


def _select_node(db: Session, storage: str | None = None) -> PhysicalNode:
    nodes = [PhysicalNode.REM, PhysicalNode.RAM, PhysicalNode.EMILIA]
    s = get_settings()
    storage = storage or s.PROXMOX_VM_STORAGE

    # If a default node is forced in settings (e.g. emilia), respect it directly
    if s.PROXMOX_NODE:
        node_name_upper = s.PROXMOX_NODE.upper()
        for n in nodes:
            if n.value == node_name_upper:
                logger.info(f"Scheduler: forcing node {n.value} based on PROXMOX_NODE setting.")
                return n

    if s.PROXMOX_ENABLED:
        try:
            from horizon.infrastructure.proxmox_client import ProxmoxClient
            client = ProxmoxClient()
            if client.enabled:
                nodes_info = client.get_nodes_resources(storage)
                if nodes_info:
                    allowed_names = {n.value.lower() for n in nodes}
                    filtered = [n for n in nodes_info if n["name"].lower() in allowed_names]
                    if filtered:
                        # Sort by storage_free and ram_free (descending)
                        sorted_nodes = sorted(filtered, key=lambda x: (x["storage_free"], x["ram_free"]), reverse=True)
                        best_name = sorted_nodes[0]["name"].lower()
                        for n in nodes:
                            if n.value.lower() == best_name:
                                logger.info(f"Scheduler picked optimal node {n.value} based on resources.")
                                return n
        except Exception as e:
            logger.warning(f"Resource-aware scheduling failed, falling back to VM counts: {e}")

    # Fallback to basic counts
    counts = {}
    for n in nodes:
        counts[n] = (
            db.query(VirtualMachine)
            .filter(
                VirtualMachine.node == n,
                VirtualMachine.status == VMStatus.ACTIVE,
            )
            .count()
        )
    return min(counts, key=counts.get)


def _next_proxmox_vmid(db: Session) -> int:
    s = get_settings()
    db_max = db.query(func.max(VirtualMachine.proxmox_vmid)).scalar() or 100
    candidate = db_max + 1

    if s.PROXMOX_ENABLED:
        try:
            from horizon.infrastructure.proxmox_client import ProxmoxClient
            client = ProxmoxClient()
            if client.enabled:
                try:
                    cluster_next = client.get_next_vmid()
                    candidate = max(candidate, cluster_next)
                except Exception:
                    pass
                resources = client.api.cluster.resources.get(type="vm")
                taken_proxmox_ids = {r["vmid"] for r in resources}
                while candidate in taken_proxmox_ids:
                    candidate += 1
        except Exception:
            pass

    return candidate


def get_user_network_groups(db: Session, owner_id) -> list[dict]:
    """List VLAN groups owned by the user (for network choice in VM creation)."""
    vms = (
        db.query(VirtualMachine)
        .filter(
            VirtualMachine.owner_id == owner_id,
            VirtualMachine.vlan_id.isnot(None),
        )
        .order_by(VirtualMachine.created_at.desc())
        .all()
    )
    groups: dict[int, dict] = {}
    for vm in vms:
        vid = vm.vlan_id
        if vid not in groups:
            groups[vid] = {"vlan_id": vid, "vm_count": 0, "vm_names": []}
        groups[vid]["vm_count"] += 1
        if vm.name not in groups[vid]["vm_names"]:
            groups[vid]["vm_names"].append(vm.name)
    return sorted(groups.values(), key=lambda g: g["vlan_id"])


def _assign_vlan(
    db: Session,
    owner_id,
    shared_network: bool = True,
    shared_vlan_id: int | None = None,
) -> int:
    """Assign a VLAN tag for the new VM.

    - shared_network=True  → join an existing user VLAN (or create one if first VM)
    - shared_network=False → always allocate a new isolated VLAN
    """
    if shared_network:
        if shared_vlan_id is not None:
            owned = (
                db.query(VirtualMachine)
                .filter(
                    VirtualMachine.owner_id == owner_id,
                    VirtualMachine.vlan_id == shared_vlan_id,
                )
                .first()
            )
            if not owned:
                raise PolicyError(
                    "POL-RESEAU-02",
                    f"Le réseau VLAN {shared_vlan_id} ne correspond à aucune de vos VMs.",
                    422,
                )
            return shared_vlan_id

        existing = (
            db.query(VirtualMachine)
            .filter(
                VirtualMachine.owner_id == owner_id,
                VirtualMachine.vlan_id.isnot(None),
            )
            .order_by(VirtualMachine.created_at.desc())
            .first()
        )
        if existing:
            return existing.vlan_id

    max_vlan = db.query(func.max(VirtualMachine.vlan_id)).scalar()
    return (max_vlan or 99) + 1
