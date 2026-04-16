"""
Routes /api/v1/admin (v2).

Nouveautés :
  PATCH  /admin/isos/{id}/validate     — valider une ISO PENDING_ANALYST
  PATCH  /admin/isos/{id}/reject       — rejeter une ISO
  DELETE /admin/isos/{id}              — supprimer une ISO (si non utilisée)
  GET    /admin/isos                   — toutes les ISOs (admin)
  GET    /admin/cluster/summary        — ressources globales cluster
  GET    /admin/cluster/nodes          — nœuds live
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from horizon.features.admin import schemas
from horizon.features.admin import service as admin_service
from horizon.features.vms import service as vm_service
from horizon.infrastructure.database import get_db
from horizon.infrastructure.email_service import send_vm_force_stopped
from horizon.shared.audit_service import log_action
from horizon.shared.dependencies import AdminUser
from horizon.shared.models import (
    AuditAction,
    AuditLog,
    IncidentStatus,
    QuotaViolation,
    SecurityIncident,
    User,
)
from horizon.shared.policies.enforcer import PolicyError

router = APIRouter(prefix="/admin", tags=["Administration"])


def _pe(exc: PolicyError):
    raise HTTPException(status_code=exc.http_status, detail=exc.message)


# ─────────────────────────── ISO Admin ─────────────────────────────────────

@router.get(
    "/isos",
    response_model=schemas.ISOAdminListResponse,
    summary="[Admin] Toutes les ISOs (tous statuts)",
)
def admin_list_isos(admin: AdminUser, db: Session = Depends(get_db)):
    items = admin_service.list_all_isos(db)
    return schemas.ISOAdminListResponse(
        items=[schemas.ISOAdminResponse.model_validate(i) for i in items],
        total=len(items),
    )


@router.patch(
    "/isos/{iso_id}/validate",
    response_model=schemas.ISOAdminResponse,
    summary="[Admin] Valider une ISO (PENDING_ANALYST → VALIDATED)",
)
def validate_iso(
    iso_id: uuid.UUID,
    body: schemas.ISOValidateRequest,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    try:
        iso = admin_service.validate_iso(db, iso_id, admin.id, note=body.note)
    except PolicyError as exc:
        _pe(exc)
    return schemas.ISOAdminResponse.model_validate(iso)


@router.patch(
    "/isos/{iso_id}/reject",
    response_model=schemas.ISOAdminResponse,
    summary="[Admin] Rejeter une ISO",
)
def reject_iso(
    iso_id: uuid.UUID,
    body: schemas.ISORejectRequest,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    try:
        iso = admin_service.reject_iso(db, iso_id, admin.id, reason=body.reason)
    except PolicyError as exc:
        _pe(exc)
    return schemas.ISOAdminResponse.model_validate(iso)


@router.delete(
    "/isos/{iso_id}",
    status_code=204,
    summary="[Admin] Supprimer une ISO (si aucune VM active ne l'utilise)",
)
def delete_iso(
    iso_id: uuid.UUID,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    try:
        admin_service.delete_iso(db, iso_id, admin.id)
    except PolicyError as exc:
        _pe(exc)


# ─────────────────────────── Cluster Monitoring ────────────────────────────

@router.get(
    "/cluster/summary",
    response_model=schemas.ClusterSummaryResponse,
    summary="[Admin] Résumé global des ressources du cluster Proxmox",
)
def cluster_summary(admin: AdminUser, db: Session = Depends(get_db)):
    try:
        data = admin_service.get_cluster_summary(db)
    except PolicyError as exc:
        _pe(exc)

    nodes = [schemas.NodeInfoResponse(**n) for n in data.get("nodes", [])]
    return schemas.ClusterSummaryResponse(
        nodes=nodes,
        total_nodes=data.get("total_nodes", 0),
        total_vms=data.get("total_vms_proxmox", 0),
    )


@router.get(
    "/cluster/nodes",
    summary="[Admin] Liste live des nœuds Proxmox avec ressources",
)
def cluster_nodes(admin: AdminUser, db: Session = Depends(get_db)):
    try:
        nodes = admin_service.get_cluster_nodes(db)
    except PolicyError as exc:
        _pe(exc)
    return {"nodes": nodes, "total": len(nodes)}


# ─────────────────────────── VM Dashboard ──────────────────────────────────

@router.get(
    "/vms",
    response_model=schemas.AdminVMListResponse,
    summary="[Admin] Dashboard global — toutes les VMs",
)
def admin_list_vms(admin: AdminUser, db: Session = Depends(get_db)):
    data = admin_service.build_admin_vm_dashboard(db)
    return schemas.AdminVMListResponse(
        items=[schemas.AdminVMResponse.model_validate(v) for v in data["items"]],
        total=data["total"],
    )


@router.post(
    "/vms/{vm_id}/stop",
    response_model=schemas.AdminForceStopResponse,
    summary="[Admin] Arrêt forcé d'une VM",
)
def admin_force_stop(
    vm_id: uuid.UUID,
    body: schemas.ForceStopRequest,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    try:
        vm = admin_service.get_vm_or_404(db, vm_id)
        owner = db.query(User).filter(User.id == vm.owner_id).first()
        vm_name = vm.name

        upid = vm_service.stop_vm(db, vm_id, admin.id, admin.role.value, force=True)
    except PolicyError as exc:
        _pe(exc)

    if owner:
        send_vm_force_stopped(owner.email, vm_name, body.reason or "Arrêt administratif")

    return schemas.AdminForceStopResponse(
        message=f"VM '{vm_name}' arrêtée de force.", upid=upid
    )


@router.delete(
    "/vms/{vm_id}",
    status_code=204,
    summary="[Admin] Suppression administrative d'une VM",
)
def admin_delete_vm(vm_id: uuid.UUID, admin: AdminUser, db: Session = Depends(get_db)):
    try:
        vm_service.delete_vm(db, vm_id, admin.id, admin.role.value)
    except PolicyError as exc:
        _pe(exc)


# ─────────────────────────── Quota Override ────────────────────────────────

@router.post(
    "/quota-override",
    response_model=schemas.QuotaOverrideMessageResponse,
    summary="[Admin] Override de quota individuel",
)
def apply_quota_override(
    body: schemas.QuotaOverrideRequest,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    admin_service.apply_quota_override(db, body, admin.id)
    log_action(
        db, admin.id, AuditAction.QUOTA_OVERRIDE_GRANTED, "user",
        uuid.UUID(body.user_id), metadata={"reason": body.reason},
    )
    db.commit()
    return schemas.QuotaOverrideMessageResponse(message="Override de quota appliqué.")


# ─────────────────────────── Audit & Incidents ─────────────────────────────

@router.get(
    "/audit-logs",
    response_model=schemas.AuditLogListResponse,
    summary="[Admin] Journal d'audit",
)
def get_audit_logs(
    admin: AdminUser,
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    action: str | None = Query(None),
    target_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == AuditAction(action))
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)
    rows = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
    return schemas.AuditLogListResponse(
        items=[schemas.AuditLogResponse.model_validate(r) for r in rows],
        limit=limit,
        offset=offset,
    )


@router.get(
    "/incidents",
    response_model=schemas.SecurityIncidentListResponse,
    summary="[Admin] Incidents de sécurité",
)
def get_incidents(
    admin: AdminUser,
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(SecurityIncident)
    if status:
        q = q.filter(SecurityIncident.status == IncidentStatus(status))
    rows = q.order_by(SecurityIncident.created_at.desc()).all()
    return schemas.SecurityIncidentListResponse(
        items=[schemas.SecurityIncidentResponse.model_validate(r) for r in rows]
    )


@router.get(
    "/violations",
    response_model=schemas.QuotaViolationListResponse,
    summary="[Admin] Violations de quota",
)
def get_violations(
    admin: AdminUser,
    resolved: bool | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(QuotaViolation)
    if resolved is not None:
        q = q.filter(QuotaViolation.resolved == resolved)
    rows = q.order_by(QuotaViolation.created_at.desc()).all()
    return schemas.QuotaViolationListResponse(
        items=[schemas.QuotaViolationResponse.model_validate(r) for r in rows]
    )


# ─────────────────────────── Proxmox Ops Directes ──────────────────────────

@router.post(
    "/proxmox/vms/{proxmox_vmid}/pause",
    response_model=schemas.ProxmoxOperationResponse,
    summary="[Admin] Suspendre une VM Proxmox",
)
def admin_proxmox_pause(
    proxmox_vmid: int, admin: AdminUser, db: Session = Depends(get_db)
):
    try:
        result = admin_service.admin_proxmox_pause_by_vmid(db, proxmox_vmid)
    except PolicyError as exc:
        _pe(exc)
    return schemas.ProxmoxOperationResponse(**result)


@router.get(
    "/proxmox/node/{node_name}/qemu",
    response_model=schemas.ProxmoxQemuListResponse,
    summary="[Admin] Liste QEMU brute sur un nœud",
)
def admin_proxmox_list_qemu(
    node_name: str, admin: AdminUser, db: Session = Depends(get_db)
):
    try:
        result = admin_service.admin_proxmox_list_qemu(db, node_name)
    except PolicyError as exc:
        _pe(exc)
    return schemas.ProxmoxQemuListResponse(**result)


@router.get(
    "/proxmox/vms/{proxmox_vmid}/status",
    response_model=schemas.ProxmoxVmStatusResponse,
    summary="[Admin] Statut courant Proxmox d'une VM",
)
def admin_proxmox_status(
    proxmox_vmid: int, admin: AdminUser, db: Session = Depends(get_db)
):
    try:
        result = admin_service.admin_proxmox_vm_status(db, proxmox_vmid)
    except PolicyError as exc:
        _pe(exc)
    return schemas.ProxmoxVmStatusResponse(**result)


# ─────────────────────────── ISO ↔ Template Mapping ───────────────────────

@router.get(
    "/proxmox/iso-templates",
    response_model=schemas.IsoProxmoxTemplateListResponse,
    summary="[Admin] Correspondances ISO → template VMID",
)
def list_iso_templates(admin: AdminUser, db: Session = Depends(get_db)):
    result = admin_service.list_iso_proxmox_templates(db)
    return schemas.IsoProxmoxTemplateListResponse(
        items=[schemas.IsoProxmoxTemplateResponse.model_validate(t) for t in result["items"]]
    )


@router.post(
    "/proxmox/iso-templates",
    response_model=schemas.IsoProxmoxTemplateResponse,
    status_code=201,
    summary="[Admin] Créer correspondance ISO → template",
)
def create_iso_template(
    body: schemas.IsoProxmoxTemplateCreate,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    try:
        tpl = admin_service.create_iso_proxmox_template(db, body)
    except PolicyError as exc:
        _pe(exc)
    return schemas.IsoProxmoxTemplateResponse.model_validate(tpl)


@router.patch(
    "/proxmox/iso-templates/{template_id}",
    response_model=schemas.IsoProxmoxTemplateResponse,
    summary="[Admin] Mettre à jour template VMID pour une ISO",
)
def patch_iso_template(
    template_id: uuid.UUID,
    body: schemas.IsoProxmoxTemplatePatch,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    try:
        tpl = admin_service.patch_iso_proxmox_template(db, template_id, body)
    except PolicyError as exc:
        _pe(exc)
    return schemas.IsoProxmoxTemplateResponse.model_validate(tpl)
