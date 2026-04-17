"""
VM Service — Logique métier (v2).

Parcours A : deploy_from_template (clone + Cloud-Init)
Parcours B : create_manual (VM vierge + ISO)
ISO        : download_iso (cache URL), get_iso_status, list_isos
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from horizon.core.config import get_settings
from horizon.features.vms.quota_service import count_active_vms, get_effective_quota
from horizon.shared.audit_service import log_action
from horizon.shared.models import (
    AuditAction,
    ISOImage,
    Reservation,
    VirtualMachine,
    VMStatus,
)
from horizon.shared.models.iso_image import ISOStatus
from horizon.shared.models.virtual_machine import VMCreationMode
from horizon.shared.policies.enforcer import (
    PolicyError,
    enforce_hard_limits,
    enforce_iso_authorized,
    enforce_session_duration,
    enforce_vm_count_limit,
    enforce_vm_ownership,
    enforce_vm_resource_limits,
)


# ─────────────────────── Helpers ──────────────────────────────────────────

def _get_proxmox():
    """Instancie ProxmoxService ; lève PolicyError si désactivé ou KO."""
    from horizon.infrastructure.proxmox_service import ProxmoxError, ProxmoxService
    s = get_settings()
    if not s.PROXMOX_ENABLED:
        raise PolicyError("PROXMOX", "Proxmox désactivé dans la configuration.", 503)
    try:
        return ProxmoxService()
    except ProxmoxError as exc:
        raise PolicyError("PROXMOX", exc.message, exc.status_code) from exc


def _proxmox_error_to_policy(exc) -> PolicyError:
    return PolicyError("PROXMOX", exc.message, exc.status_code)


def _build_net0(vlan_id: int | None, base: str) -> str:
    # return f"{base},tag={vlan_id}" if vlan_id else base
    return base



def _next_proxmox_vmid(db: Session) -> int:
    """VMID local (fallback si Proxmox désactivé)."""
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


def _get_vm_or_404(db: Session, vm_id) -> VirtualMachine:
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise PolicyError("VM", "VM introuvable.", 404)
    return vm


def _get_iso_or_404(db: Session, iso_id) -> ISOImage:
    iso = db.query(ISOImage).filter(ISOImage.id == iso_id).first()
    if not iso:
        raise PolicyError("ISO", "Image ISO introuvable.", 404)
    return iso


# ─────────────────────── Templates ────────────────────────────────────────

def list_templates(
    db: Session,
    node: str | None = None,
    os_filter: str | None = None,
) -> list[dict]:
    """GET /api/v1/vms/templates — liste les templates Proxmox."""
    from horizon.infrastructure.proxmox_service import ProxmoxError, ProxmoxService
    s = get_settings()
    if not s.PROXMOX_ENABLED:
        return []
    try:
        svc = ProxmoxService()
        return svc.list_templates(node=node, os_filter=os_filter)
    except ProxmoxError as exc:
        raise PolicyError("PROXMOX", exc.message, exc.status_code) from exc


# ─────────────────────── Parcours A ───────────────────────────────────────

def deploy_from_template(db: Session, owner_id, data: dict) -> VirtualMachine:
    """
    POST /api/v1/vms/deploy-template

    1. Vérifie les quotas
    2. Choisit le nœud automatiquement
    3. Clone le template + injecte Cloud-Init
    4. Enregistre en BD
    """
    from horizon.infrastructure.proxmox_service import ProxmoxError

    s = get_settings()
    quota = get_effective_quota(db, owner_id)

    memory_mb = data["memory_mb"]
    ram_gb = round(memory_mb / 1024, 2)
    cores = data["cores"]
    session_hours = data["session_hours"]
    storage_gb = 0  # défini par le template, vérification non bloquante

    enforce_hard_limits(cores, ram_gb, storage_gb or 1, session_hours)
    enforce_vm_resource_limits(
        cores, ram_gb, storage_gb or 1,
        quota.max_vcpu_per_vm, quota.max_ram_gb_per_vm, quota.max_storage_gb_per_vm,
    )
    enforce_session_duration(session_hours, quota.max_session_duration_hours)

    active_count = count_active_vms(db, owner_id)
    enforce_vm_count_limit(active_count, quota.max_simultaneous_vms)

    vlan_id = _assign_vlan(db, owner_id)

    # Sélection du nœud
    svc = _get_proxmox()
    try:
        node = svc.pick_node(strategy=data.get("node_strategy", "least_vms"))
        vmid = svc.next_free_vmid()
    except ProxmoxError as exc:
        raise _proxmox_error_to_policy(exc) from exc

    ci = data.get("cloud_init", {})
    net0 = _build_net0(vlan_id, data.get("net0", s.PROXMOX_NET0_TEMPLATE))

    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        proxmox_vmid=vmid,
        name=data["vm_name"],
        owner_id=owner_id,
        proxmox_node=node,
        vcpu=cores,
        ram_gb=ram_gb,
        storage_gb=storage_gb,
        template_vmid=data["template_vmid"],
        creation_mode=VMCreationMode.TEMPLATE,
        status=VMStatus.PENDING,
        lease_start=now,
        lease_end=now + timedelta(hours=session_hours),
        vlan_id=vlan_id,
        cloudinit_user=ci.get("user"),
        shared_space_gb=0.0,
    )
    db.add(vm)
    db.add(
        Reservation(
            id=uuid.uuid4(),
            vm_id=vm.id,
            user_id=owner_id,
            start_time=vm.lease_start,
            end_time=vm.lease_end,
        )
    )

    try:
        db.flush()

        try:
            upid = svc.deploy_from_template(
                node=node,
                template_vmid=data["template_vmid"],
                new_vmid=vmid,
                vm_name=data["vm_name"],
                memory_mb=memory_mb,
                cores=cores,
                disk_storage=data.get("disk_storage", "local-lvm"),
                net0=net0,
                ci_user=ci.get("user"),
                ci_ssh_keys=ci.get("ssh_key"),
                ci_password=ci.get("password"),
                ci_ip_config=ci.get("ip_config"),
            )
        except ProxmoxError as exc:
            raise _proxmox_error_to_policy(exc) from exc

        vm.last_upid = upid
        vm.status = VMStatus.ACTIVE

        log_action(
            db, owner_id, AuditAction.VM_CREATED, "vm", vm.id,
            metadata={
                "mode": "template",
                "template_vmid": data["template_vmid"],
                "node": node,
            },
        )
        db.commit()
        db.refresh(vm)
        return vm

    except PolicyError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


# ─────────────────────── Parcours B ───────────────────────────────────────

def create_manual(db: Session, owner_id, data: dict) -> VirtualMachine:
    """
    POST /api/v1/vms/create-manual

    1. Vérifie que l'ISO est VALIDATED
    2. Choisit le nœud automatiquement
    3. Crée la VM vierge sur Proxmox et monte l'ISO
    4. Enregistre en BD
    """
    from horizon.infrastructure.proxmox_service import ProxmoxError

    s = get_settings()
    iso = _get_iso_or_404(db, data["iso_id"])

    if iso.status != ISOStatus.VALIDATED:
        raise PolicyError(
            "ISO",
            f"L'ISO '{iso.name}' n'est pas encore validée (statut : {iso.status.value}).",
            403,
        )
    enforce_iso_authorized(iso.is_active)

    quota = get_effective_quota(db, owner_id)
    enforce_hard_limits(data["vcpu"], data["ram_gb"], data["storage_gb"], data["session_hours"])
    enforce_vm_resource_limits(
        data["vcpu"], data["ram_gb"], data["storage_gb"],
        quota.max_vcpu_per_vm, quota.max_ram_gb_per_vm, quota.max_storage_gb_per_vm,
    )
    enforce_session_duration(data["session_hours"], quota.max_session_duration_hours)
    enforce_vm_count_limit(count_active_vms(db, owner_id), quota.max_simultaneous_vms)

    vlan_id = _assign_vlan(db, owner_id)
    svc = _get_proxmox()

    try:
        node = svc.pick_node(strategy=data.get("node_strategy", "least_vms"))
        vmid = svc.next_free_vmid()
    except ProxmoxError as exc:
        raise _proxmox_error_to_policy(exc) from exc

    # Chemin de l'ISO sur Proxmox (ex: "local:iso/ubuntu-22.04.iso")
    if not iso.proxmox_node or not iso.proxmox_storage:
        raise PolicyError(
            "ISO",
            "L'ISO ne dispose pas d'informations de stockage Proxmox. Contactez l'admin.",
            409,
        )
    iso_path = f"{iso.proxmox_storage}:iso/{iso.filename}"
    net0 = _build_net0(vlan_id, data.get("net0", s.PROXMOX_NET0_TEMPLATE))
    memory_mb = max(512, int(data["ram_gb"] * 1024))

    now = datetime.now(timezone.utc)
    vm = VirtualMachine(
        id=uuid.uuid4(),
        proxmox_vmid=vmid,
        name=data["vm_name"],
        description=data.get("description"),
        owner_id=owner_id,
        proxmox_node=node,
        vcpu=data["vcpu"],
        ram_gb=data["ram_gb"],
        storage_gb=data["storage_gb"],
        iso_image_id=iso.id,
        creation_mode=VMCreationMode.MANUAL,
        status=VMStatus.PENDING,
        lease_start=now,
        lease_end=now + timedelta(hours=data["session_hours"]),
        vlan_id=vlan_id,
        shared_space_gb=0.0,
    )
    db.add(vm)
    db.add(
        Reservation(
            id=uuid.uuid4(),
            vm_id=vm.id,
            user_id=owner_id,
            start_time=vm.lease_start,
            end_time=vm.lease_end,
        )
    )

    try:
        db.flush()

        try:
            upid = svc.create_vm_manual(
                node=node,
                vmid=vmid,
                vm_name=data["vm_name"],
                memory_mb=memory_mb,
                cores=data["vcpu"],
                disk_size_gb=data["storage_gb"],
                disk_storage=data.get("disk_storage", "local-lvm"),
                iso_path=iso_path,
                net0=net0,
                bios=data.get("bios", "seabios"),
                ostype=data.get("ostype", "l26"),
            )
        except ProxmoxError as exc:
            raise _proxmox_error_to_policy(exc) from exc

        vm.last_upid = upid
        vm.status = VMStatus.ACTIVE

        log_action(
            db, owner_id, AuditAction.VM_CREATED, "vm", vm.id,
            metadata={"mode": "manual", "iso": iso.filename, "node": node},
        )
        db.commit()
        db.refresh(vm)
        return vm

    except PolicyError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


# ─────────────────────── ISO Management ───────────────────────────────────

def download_iso(db: Session, requester_id, data: dict) -> ISOImage:
    """
    POST /api/v1/vms/isos/download

    - Cache : si l'URL existe déjà (status VALIDATED/DOWNLOADING), retourne l'entrée existante
    - Sinon : lance le téléchargement via Proxmox, crée l'entrée en BD
    """
    from horizon.infrastructure.proxmox_service import ProxmoxError

    url = data["url"]
    s = get_settings()

    # ── Cache check ──
    existing = (
        db.query(ISOImage)
        .filter(ISOImage.source_url == url)
        .filter(ISOImage.status.in_([ISOStatus.VALIDATED, ISOStatus.DOWNLOADING, ISOStatus.PENDING_ANALYST]))
        .first()
    )
    if existing:
        return existing

    # ── Nouveau téléchargement ──
    svc = _get_proxmox()
    storage = data.get("storage", "local")

    # Choisir le nœud pour héberger l'ISO (premier nœud disponible)
    try:
        node = svc.pick_node("least_vms")
    except ProxmoxError as exc:
        raise _proxmox_error_to_policy(exc) from exc

    iso = ISOImage(
        id=uuid.uuid4(),
        name=data["name"],
        filename=data["filename"],
        os_family=data["os_family"],
        os_version=data["os_version"],
        description=data.get("description"),
        source_url=url,
        status=ISOStatus.DOWNLOADING,
        is_active=False,
        created_by_id=requester_id,
        proxmox_node=node,
        proxmox_storage=storage,
    )
    db.add(iso)

    try:
        db.flush()

        try:
            upid = svc.download_iso_url(
                node=node,
                storage=storage,
                url=url,
                filename=data["filename"],
                checksum=data.get("checksum"),
                checksum_algorithm=data.get("checksum_algorithm", "sha256"),
            )
        except ProxmoxError as exc:
            db.rollback()
            raise _proxmox_error_to_policy(exc) from exc

        iso.proxmox_upid = upid
        db.commit()
        db.refresh(iso)
        return iso

    except PolicyError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


def get_iso_status(db: Session, iso_id, requester_id, requester_role: str) -> dict:
    """
    GET /api/v1/vms/isos/{iso_id}/status

    Interroge Proxmox pour le statut de la tâche et met à jour la BD.
    """
    from horizon.infrastructure.proxmox_service import ProxmoxError, ProxmoxService

    iso = _get_iso_or_404(db, iso_id)

    # Vérification de visibilité (PENDING_ANALYST = créateur + admin seulement)
    _check_iso_visibility(iso, requester_id, requester_role)

    result: dict[str, Any] = {
        "iso_id": iso.id,
        "filename": iso.filename,
        "status": iso.status.value,
        "upid": iso.proxmox_upid,
        "error_message": iso.error_message,
        "proxmox_task_status": None,
        "proxmox_task_exit": None,
        "progress_pct": None,
    }

    if not iso.proxmox_upid or not iso.proxmox_node:
        return result

    s = get_settings()
    if not s.PROXMOX_ENABLED:
        return result

    try:
        svc = ProxmoxService()
        task = svc.get_task_status(iso.proxmox_node, iso.proxmox_upid)

        result["proxmox_task_status"] = task.status
        result["proxmox_task_exit"] = task.exit_status
        result["progress_pct"] = task.pct

        # Mise à jour automatique du statut en BD
        if task.status == "stopped":
            if task.exit_status == "OK":
                if iso.status == ISOStatus.DOWNLOADING:
                    iso.status = ISOStatus.PENDING_ANALYST
                    db.commit()
                    result["status"] = ISOStatus.PENDING_ANALYST.value
            else:
                iso.status = ISOStatus.ERROR
                iso.error_message = task.exit_status
                db.commit()
                result["status"] = ISOStatus.ERROR.value
                result["error_message"] = task.exit_status

    except ProxmoxError as exc:
        # Ne pas propager — retourner le statut BD sans crash
        result["proxmox_task_status"] = f"error: {exc.message}"

    return result


def list_isos(db: Session, requester_id, requester_role: str) -> list[ISOImage]:
    """
    GET /api/v1/vms/isos

    - Admin / Super Admin : toutes les ISOs
    - Utilisateur normal  : ISOs VALIDATED + ses propres PENDING_ANALYST
    """
    if requester_role in ("ADMIN", "SUPER_ADMIN"):
        return db.query(ISOImage).order_by(ISOImage.created_at.desc()).all()

    from sqlalchemy import or_
    return (
        db.query(ISOImage)
        .filter(
            or_(
                ISOImage.status == ISOStatus.VALIDATED,
                (ISOImage.status == ISOStatus.PENDING_ANALYST) & (ISOImage.created_by_id == requester_id),
            )
        )
        .order_by(ISOImage.created_at.desc())
        .all()
    )


def _check_iso_visibility(iso: ISOImage, requester_id, requester_role: str) -> None:
    if requester_role in ("ADMIN", "SUPER_ADMIN"):
        return
    if iso.status == ISOStatus.VALIDATED:
        return
    if iso.created_by_id == requester_id:
        return
    raise PolicyError("ISO", "ISO non accessible.", 403)


# ─────────────────────── Opérations VM communes ───────────────────────────

def stop_vm(db: Session, vm_id, requesting_user_id, user_role: str, force: bool = False) -> str | None:
    from horizon.infrastructure.proxmox_service import ProxmoxError, ProxmoxService

    vm = _get_vm_or_404(db, vm_id)
    if not force:
        enforce_vm_ownership(vm.owner_id, requesting_user_id, user_role)
    if vm.status == VMStatus.STOPPED:
        raise PolicyError("VM", "Cette VM est déjà arrêtée.", 409)

    s = get_settings()
    upid = None
    if s.PROXMOX_ENABLED:
        try:
            svc = ProxmoxService()
            upid = svc.shutdown_vm(vm.proxmox_node, vm.proxmox_vmid)
        except ProxmoxError as exc:
            raise _proxmox_error_to_policy(exc) from exc

    vm.status = VMStatus.STOPPED
    vm.stopped_at = datetime.now(timezone.utc)
    if upid:
        vm.last_upid = upid

    log_action(
        db, requesting_user_id,
        AuditAction.VM_FORCE_STOPPED if force else AuditAction.VM_STOPPED,
        "vm", vm.id, metadata={"force": force},
    )
    db.commit()
    return upid


def delete_vm(db: Session, vm_id, requesting_user_id, user_role: str) -> None:
    from horizon.infrastructure.proxmox_service import ProxmoxError, ProxmoxService

    vm = _get_vm_or_404(db, vm_id)
    enforce_vm_ownership(vm.owner_id, requesting_user_id, user_role)

    s = get_settings()
    if s.PROXMOX_ENABLED:
        try:
            svc = ProxmoxService()
            if vm.status == VMStatus.ACTIVE:
                try:
                    svc.stop_vm(vm.proxmox_node, vm.proxmox_vmid)
                except ProxmoxError:
                    pass  # Arrêt best-effort avant suppression
            svc.delete_vm(vm.proxmox_node, vm.proxmox_vmid)
        except ProxmoxError as exc:
            raise _proxmox_error_to_policy(exc) from exc

    is_admin = user_role in ("ADMIN", "SUPER_ADMIN")
    log_action(
        db, requesting_user_id,
        AuditAction.VM_ADMIN_DELETED if is_admin else AuditAction.VM_DELETED,
        "vm", vm.id,
    )
    db.delete(vm)
    db.commit()


def get_user_vms(db: Session, user_id) -> list[VirtualMachine]:
    return db.query(VirtualMachine).filter(VirtualMachine.owner_id == user_id).all()


def get_all_vms_admin(db: Session) -> list[VirtualMachine]:
    return db.query(VirtualMachine).all()


def extend_vm_lease(
    db: Session, vm_id, requesting_user_id, user_role: str, additional_hours: int
) -> VirtualMachine:
    vm = _get_vm_or_404(db, vm_id)
    enforce_vm_ownership(vm.owner_id, requesting_user_id, user_role)

    quota = get_effective_quota(db, vm.owner_id)
    total_hours = int((vm.lease_end - vm.lease_start).total_seconds() / 3600) + additional_hours
    enforce_session_duration(total_hours, quota.max_session_duration_hours)

    old_end = vm.lease_end
    vm.lease_end = vm.lease_end + timedelta(hours=additional_hours)

    db.add(
        Reservation(
            id=uuid.uuid4(),
            vm_id=vm.id,
            user_id=requesting_user_id,
            start_time=old_end,
            end_time=vm.lease_end,
            extended=True,
        )
    )
    log_action(
        db, requesting_user_id, AuditAction.VM_LEASE_EXTENDED, "vm", vm.id,
        metadata={"additional_hours": additional_hours, "new_end": vm.lease_end.isoformat()},
    )
    db.commit()
    db.refresh(vm)
    return vm
