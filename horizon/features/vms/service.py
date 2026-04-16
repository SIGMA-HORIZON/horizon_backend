"""Cycle de vie des VMs."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from horizon.core.config import get_settings
from horizon.features.vms.quota_service import count_active_vms, get_effective_quota
from horizon.shared.audit_service import log_action
from horizon.shared.models import (
    AuditAction,
    ISOImage,
    IsoProxmoxTemplate,
    PhysicalNode,
    ProxmoxNodeMapping,
    Reservation,
    VirtualMachine,
    VMStatus,
)
from horizon.shared.policies.enforcer import (
    PolicyError,
    enforce_hard_limits,
    enforce_iso_authorized,
    enforce_session_duration,
    enforce_vm_count_limit,
    enforce_vm_ownership,
    enforce_vm_resource_limits,
)


def _resolve_proxmox_node_name(db: Session, physical_node: PhysicalNode) -> str:
    s = get_settings()
    row = (
        db.query(ProxmoxNodeMapping)
        .filter(ProxmoxNodeMapping.physical_node == physical_node)
        .first()
    )
    if row:
        return row.proxmox_node_name
    if s.PROXMOX_DEFAULT_NODE:
        return s.PROXMOX_DEFAULT_NODE
    raise PolicyError(
        "PROXMOX",
        "Aucun mapping nœud Proxmox pour ce nœud métier (table proxmox_node_mappings).",
        500,
    )


def _build_net0(vlan_id: int | None) -> str:
    s = get_settings()
    base = s.PROXMOX_NET0_TEMPLATE.strip()
    if vlan_id is not None:
        return f"{base},tag={vlan_id}"
    return base


def create_vm(db: Session, owner_id, data: dict) -> VirtualMachine:
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
    vlan_id = _assign_vlan(db, owner_id)

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
                client.create_vm_from_template(
                    px_node,
                    tpl.proxmox_template_vmid,
                    vm.proxmox_vmid,
                    data["name"],
                    memory_mb,
                    data["vcpu"],
                    net0,
                )
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


def stop_vm(db: Session, vm_id, requesting_user_id, user_role: str, force: bool = False) -> None:
    from horizon.infrastructure.proxmox_client import ProxmoxClient, ProxmoxIntegrationError

    vm = _get_vm_or_404(db, vm_id)

    if not force:
        enforce_vm_ownership(vm.owner_id, requesting_user_id, user_role)

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
                client.stop_vm(px_node, vm.proxmox_vmid)
            except ProxmoxIntegrationError as e:
                raise PolicyError("PROXMOX", e.message, e.status_code) from e

    vm.status = VMStatus.STOPPED
    vm.stopped_at = datetime.now(timezone.utc)

    action = AuditAction.VM_FORCE_STOPPED if force else AuditAction.VM_STOPPED
    log_action(db, requesting_user_id, action, "vm",
               vm.id, metadata={"force": force})
    db.commit()


def delete_vm(db: Session, vm_id, requesting_user_id, user_role: str) -> None:
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
                        client.stop_vm(px_node, vm.proxmox_vmid)
                    except ProxmoxIntegrationError:
                        pass
                client.delete_vm(px_node, vm.proxmox_vmid)
            except ProxmoxIntegrationError as e:
                raise PolicyError("PROXMOX", e.message, e.status_code) from e

    log_action(db, requesting_user_id, action, "vm", vm.id)
    db.delete(vm)
    db.commit()


def update_vm(db: Session, vm_id, requesting_user_id, user_role: str, data: dict) -> VirtualMachine:
    vm = _get_vm_or_404(db, vm_id)
    enforce_vm_ownership(vm.owner_id, requesting_user_id, user_role)

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


def extend_vm_lease(
    db: Session, vm_id, requesting_user_id, user_role: str, additional_hours: int
) -> VirtualMachine:
    vm = _get_vm_or_404(db, vm_id)
    enforce_vm_ownership(vm.owner_id, requesting_user_id, user_role)

    quota = get_effective_quota(db, vm.owner_id)
    total_hours = int(
        (vm.lease_end - vm.lease_start).total_seconds() / 3600) + additional_hours
    enforce_session_duration(total_hours, quota.max_session_duration_hours)

    old_end = vm.lease_end
    vm.lease_end = vm.lease_end + timedelta(hours=additional_hours)

    ext_reservation = Reservation(
        id=uuid.uuid4(),
        vm_id=vm.id,
        user_id=requesting_user_id,
        start_time=old_end,
        end_time=vm.lease_end,
        extended=True,
    )
    db.add(ext_reservation)

    log_action(
        db,
        requesting_user_id,
        AuditAction.VM_LEASE_EXTENDED,
        "vm",
        vm.id,
        metadata={"additional_hours": additional_hours,
                  "new_end": vm.lease_end.isoformat()},
    )
    db.commit()
    db.refresh(vm)
    return vm


def get_user_vms(db: Session, user_id) -> list[VirtualMachine]:
    return db.query(VirtualMachine).filter(VirtualMachine.owner_id == user_id).all()


def get_all_vms_admin(db: Session) -> list[VirtualMachine]:
    return db.query(VirtualMachine).all()


def _get_vm_or_404(db: Session, vm_id) -> VirtualMachine:
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise PolicyError("VM", "VM introuvable.", 404)
    return vm


def _select_node(db: Session) -> PhysicalNode:
    nodes = [PhysicalNode.REM, PhysicalNode.RAM, PhysicalNode.EMILIA]
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
    max_id = db.query(func.max(VirtualMachine.proxmox_vmid)).scalar()
    return (max_id or 100) + 1


def _assign_vlan(db: Session, owner_id) -> int:
    existing = (
        db.query(VirtualMachine)
        .filter(
            VirtualMachine.owner_id == owner_id,
            VirtualMachine.vlan_id.isnot(None),
        )
        .first()
    )
    if existing:
        return existing.vlan_id
    max_vlan = db.query(func.max(VirtualMachine.vlan_id)).scalar()
    return (max_vlan or 99) + 1
