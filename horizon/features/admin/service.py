"""
Admin Service (v2).

Fonctionnalités :
- Validation / rejet d'ISOs (PATCH /admin/isos/{id}/validate|reject)
- Monitoring ressources cluster Proxmox
- Gestion nœuds (liste live depuis Proxmox)
- Dashboard VMs admin
- Opérations Proxmox directes (pause, status, list qemu)
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from horizon.core.config import get_settings
from horizon.shared.audit_service import log_action
from horizon.shared.models import (
    AuditAction,
    ISOImage,
    IsoProxmoxTemplate,
    VirtualMachine,
    VMStatus,
)
from horizon.shared.models.iso_image import ISOStatus
from horizon.shared.policies.enforcer import PolicyError


# ─────────────────────── Helpers ──────────────────────────────────────────

def _get_iso_or_404(db: Session, iso_id) -> ISOImage:
    iso = db.query(ISOImage).filter(ISOImage.id == iso_id).first()
    if not iso:
        raise PolicyError("ISO", "ISO introuvable.", 404)
    return iso


def _get_proxmox():
    from horizon.infrastructure.proxmox_service import ProxmoxError, ProxmoxService
    s = get_settings()
    if not s.PROXMOX_ENABLED:
        raise PolicyError("PROXMOX", "Proxmox désactivé dans la configuration.", 503)
    try:
        return ProxmoxService()
    except ProxmoxError as exc:
        raise PolicyError("PROXMOX", exc.message, exc.status_code) from exc


def _proxmox_error(exc) -> PolicyError:
    return PolicyError("PROXMOX", exc.message, exc.status_code)


# ─────────────────────── ISO Admin ────────────────────────────────────────

def list_all_isos(db: Session) -> list[ISOImage]:
    return db.query(ISOImage).order_by(ISOImage.created_at.desc()).all()


def validate_iso(db: Session, iso_id, admin_id, note: str | None = None) -> ISOImage:
    """
    PATCH /admin/isos/{id}/validate

    Transite l'ISO vers VALIDATED et l'active pour tous les utilisateurs.
    Seul un ISO en statut PENDING_ANALYST peut être validé.
    """
    iso = _get_iso_or_404(db, iso_id)

    if iso.status == ISOStatus.VALIDATED:
        raise PolicyError("ISO", "Cette ISO est déjà validée.", 409)

    if iso.status not in (ISOStatus.PENDING_ANALYST,):
        raise PolicyError(
            "ISO",
            f"Impossible de valider une ISO en statut '{iso.status.value}'. "
            "Seul le statut PENDING_ANALYST est éligible.",
            422,
        )

    iso.status = ISOStatus.VALIDATED
    iso.is_active = True
    if note:
        iso.description = f"{iso.description or ''} [Validation: {note}]".strip()

    log_action(
        db, admin_id, AuditAction.VM_MODIFIED, "iso", iso.id,
        metadata={"action": "validate", "note": note},
    )
    db.commit()
    db.refresh(iso)
    return iso


def reject_iso(db: Session, iso_id, admin_id, reason: str) -> ISOImage:
    """
    PATCH /admin/isos/{id}/reject

    Marque l'ISO comme ERROR avec un message de rejet.
    """
    iso = _get_iso_or_404(db, iso_id)

    if iso.status == ISOStatus.VALIDATED:
        raise PolicyError("ISO", "Impossible de rejeter une ISO déjà validée.", 409)

    iso.status = ISOStatus.ERROR
    iso.is_active = False
    iso.error_message = f"Rejet administrateur : {reason}"

    log_action(
        db, admin_id, AuditAction.VM_MODIFIED, "iso", iso.id,
        metadata={"action": "reject", "reason": reason},
    )
    db.commit()
    db.refresh(iso)
    return iso


def delete_iso(db: Session, iso_id, admin_id) -> None:
    """DELETE /admin/isos/{id} — Suppression définitive (uniquement si non utilisée)."""
    iso = _get_iso_or_404(db, iso_id)

    # Vérifier qu'aucune VM n'utilise cette ISO
    vm_count = (
        db.query(VirtualMachine)
        .filter(
            VirtualMachine.iso_image_id == iso_id,
            VirtualMachine.status.in_([VMStatus.ACTIVE, VMStatus.PENDING]),
        )
        .count()
    )
    if vm_count > 0:
        raise PolicyError(
            "ISO",
            f"Impossible de supprimer : {vm_count} VM(s) active(s) utilisent cette ISO.",
            409,
        )

    log_action(db, admin_id, AuditAction.VM_ADMIN_DELETED, "iso", iso_id)
    db.delete(iso)
    db.commit()


# ─────────────────────── Cluster Monitoring ───────────────────────────────

def get_cluster_summary(db: Session) -> dict[str, Any]:
    """
    GET /admin/cluster/summary

    Ressources globales du cluster Proxmox + stats BD.
    """
    from horizon.infrastructure.proxmox_service import ProxmoxError

    result: dict[str, Any] = {
        "proxmox_available": False,
        "nodes": [],
        "total_nodes": 0,
        "total_vms_proxmox": 0,
        "db_stats": _db_vm_stats(db),
    }

    s = get_settings()
    if not s.PROXMOX_ENABLED:
        return result

    try:
        svc = _get_proxmox()
        summary = svc.cluster_resources_summary()
        result.update({
            "proxmox_available": True,
            **summary,
        })
    except (PolicyError, Exception):
        result["proxmox_available"] = False

    return result


def get_cluster_nodes(db: Session) -> list[dict[str, Any]]:
    """GET /admin/cluster/nodes — liste live des nœuds."""
    from horizon.infrastructure.proxmox_service import ProxmoxError

    s = get_settings()
    if not s.PROXMOX_ENABLED:
        return []

    try:
        svc = _get_proxmox()
        nodes = svc.list_nodes()
        return [
            {
                "name": n.name,
                "cpu_usage_pct": round(n.cpu_usage * 100, 1),
                "mem_used_gb": round(n.mem_used / (1024 ** 3), 2),
                "mem_total_gb": round(n.mem_total / (1024 ** 3), 2),
                "mem_free_gb": n.mem_free_gb,
                "vm_count": n.vm_count,
            }
            for n in nodes
        ]
    except (PolicyError, Exception):
        return []


def _db_vm_stats(db: Session) -> dict[str, int]:
    from sqlalchemy import func
    rows = (
        db.query(VirtualMachine.status, func.count(VirtualMachine.id))
        .group_by(VirtualMachine.status)
        .all()
    )
    stats = {status.value: count for status, count in rows}
    stats["total"] = sum(stats.values())
    return stats


# ─────────────────────── VM Dashboard Admin ───────────────────────────────

def build_admin_vm_dashboard(db: Session) -> dict[str, Any]:
    vms = db.query(VirtualMachine).all()
    return {
        "items": vms,
        "total": len(vms),
    }


def get_vm_or_404(db: Session, vm_id) -> VirtualMachine:
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise PolicyError("VM", "VM introuvable.", 404)
    return vm


# ─────────────────────── Proxmox Opérations Directes ──────────────────────

def admin_proxmox_pause_by_vmid(db: Session, proxmox_vmid: int) -> dict[str, Any]:
    from horizon.infrastructure.proxmox_service import ProxmoxError

    vm = db.query(VirtualMachine).filter(VirtualMachine.proxmox_vmid == proxmox_vmid).first()
    if not vm:
        raise PolicyError("VM", f"VM avec proxmox_vmid={proxmox_vmid} introuvable.", 404)

    try:
        svc = _get_proxmox()
        upid = svc.suspend_vm(vm.proxmox_node, proxmox_vmid)
    except PolicyError:
        raise
    except Exception as exc:
        raise PolicyError("PROXMOX", str(exc), 502) from exc

    vm.status = VMStatus.SUSPENDED
    db.commit()

    return {"message": f"VM {proxmox_vmid} suspendue.", "upid": upid}


def admin_proxmox_list_qemu(db: Session, node_name: str) -> dict[str, Any]:
    from horizon.infrastructure.proxmox_service import ProxmoxError

    try:
        svc = _get_proxmox()
        vms = svc.list_node_vms(node_name)
    except PolicyError:
        raise
    except ProxmoxError as exc:
        raise _proxmox_error(exc) from exc

    return {"node": node_name, "vms": vms}


def admin_proxmox_vm_status(db: Session, proxmox_vmid: int) -> dict[str, Any]:
    from horizon.infrastructure.proxmox_service import ProxmoxError

    vm = db.query(VirtualMachine).filter(VirtualMachine.proxmox_vmid == proxmox_vmid).first()
    if not vm:
        raise PolicyError("VM", f"VM proxmox_vmid={proxmox_vmid} introuvable.", 404)

    try:
        svc = _get_proxmox()
        raw = svc.get_vm_status(vm.proxmox_node, proxmox_vmid)
    except PolicyError:
        raise
    except ProxmoxError as exc:
        raise _proxmox_error(exc) from exc

    return {"proxmox_vmid": proxmox_vmid, "raw_status": raw}


# ─────────────────────── ISO ↔ Template Mapping ───────────────────────────

def list_iso_proxmox_templates(db: Session) -> dict[str, Any]:
    items = db.query(IsoProxmoxTemplate).all()
    return {"items": items}


def create_iso_proxmox_template(db: Session, body) -> IsoProxmoxTemplate:
    existing = (
        db.query(IsoProxmoxTemplate)
        .filter(IsoProxmoxTemplate.iso_image_id == uuid.UUID(body.iso_image_id))
        .first()
    )
    if existing:
        raise PolicyError("ISO", "Un mapping existe déjà pour cette ISO.", 409)

    tpl = IsoProxmoxTemplate(
        id=uuid.uuid4(),
        iso_image_id=uuid.UUID(body.iso_image_id),
        proxmox_template_vmid=body.proxmox_template_vmid,
    )
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return tpl


def patch_iso_proxmox_template(db: Session, template_id, body) -> IsoProxmoxTemplate:
    tpl = db.query(IsoProxmoxTemplate).filter(IsoProxmoxTemplate.id == template_id).first()
    if not tpl:
        raise PolicyError("ISO", "Mapping introuvable.", 404)
    if body.proxmox_template_vmid is not None:
        tpl.proxmox_template_vmid = body.proxmox_template_vmid
    db.commit()
    db.refresh(tpl)
    return tpl


# ─────────────────────── Quota Override ───────────────────────────────────

def apply_quota_override(db: Session, body, admin_id) -> None:
    from horizon.shared.models import UserQuota

    user_id = uuid.UUID(body.user_id)
    quota = db.query(UserQuota).filter(UserQuota.user_id == user_id).first()
    if not quota:
        from horizon.shared.models import UserQuota
        quota = UserQuota(id=uuid.uuid4(), user_id=user_id)
        db.add(quota)

    fields = [
        "max_vcpu_per_vm", "max_ram_gb_per_vm", "max_storage_gb_per_vm",
        "max_simultaneous_vms", "max_session_duration_hours",
    ]
    for f in fields:
        val = getattr(body, f, None)
        if val is not None:
            setattr(quota, f, val)

    db.flush()
