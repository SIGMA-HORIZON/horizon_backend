"""Routes /api/v1/admin."""

import uuid

from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session

from horizon.features.admin import schemas
from horizon.features.admin import service as admin_service
from horizon.features.vms import service as vm_service
from horizon.infrastructure.database import get_db
from horizon.infrastructure.email_service import send_vm_force_stopped
from horizon.shared.dependencies import AdminUser
from horizon.shared.audit_service import log_action
from horizon.shared.models import (
    AuditAction,
    AuditLog,
    IncidentStatus,
    QuotaViolation,
    SecurityIncident,
    User,
)

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get(
    "/vms",
    response_model=schemas.AdminVMListResponse,
    summary="[Admin] Dashboard global - toutes les VMs",
)
def admin_list_vms(admin: AdminUser, db: Session = Depends(get_db)):
    return admin_service.build_admin_vm_dashboard(db)


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
    vm = admin_service.get_vm_or_404(db, vm_id)
    owner = db.query(User).filter(User.id == vm.owner_id).first()
    vm_name = vm.name

    vm_service.stop_vm(db, vm_id, admin.id, admin.role.value, force=True)

    if owner:
        send_vm_force_stopped(owner.email, vm_name,
                              body.reason or "Arrêt administratif")

    return schemas.AdminForceStopResponse(message=f"VM {vm_name} arrêtée de force.")


@router.delete("/vms/{vm_id}", status_code=204, summary="[Admin] Suppression administrative")
def admin_delete_vm(vm_id: uuid.UUID, admin: AdminUser, db: Session = Depends(get_db)):
    vm_service.delete_vm(db, vm_id, admin.id, admin.role.value)


@router.post(
    "/quota-override",
    response_model=schemas.QuotaOverrideMessageResponse,
    summary="[Admin] Override de quota individuel",
)
def apply_quota_override(body: schemas.QuotaOverrideRequest, admin: AdminUser, db: Session = Depends(get_db)):
    admin_service.apply_quota_override(db, body, admin.id)
    log_action(
        db,
        admin.id,
        AuditAction.QUOTA_OVERRIDE_GRANTED,
        "user",
        uuid.UUID(body.user_id),
        metadata={"reason": body.reason},
    )
    db.commit()
    return schemas.QuotaOverrideMessageResponse(message="Override de quota appliqué.")


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
    rows = query.order_by(AuditLog.timestamp.desc()).offset(
        offset).limit(limit).all()
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
        items=[schemas.SecurityIncidentResponse.model_validate(
            r) for r in rows]
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


@router.post(
    "/proxmox/vms/{proxmox_vmid}/pause",
    response_model=schemas.ProxmoxOperationResponse,
    summary="[Admin] Pause Proxmox (suspend) - proxmox_vmid Horizon",
)
def admin_proxmox_pause(proxmox_vmid: int, admin: AdminUser, db: Session = Depends(get_db)):
    return admin_service.admin_proxmox_pause_by_vmid(db, proxmox_vmid)


@router.get(
    "/proxmox/node/{node_name}/qemu",
    response_model=schemas.ProxmoxQemuListResponse,
    summary="[Admin] Liste QEMU brute sur un nœud Proxmox",
)
def admin_proxmox_list_qemu(node_name: str, admin: AdminUser, db: Session = Depends(get_db)):
    return admin_service.admin_proxmox_list_qemu(db, node_name)


@router.get(
    "/proxmox/vms/{proxmox_vmid}/status",
    response_model=schemas.ProxmoxVmStatusResponse,
    summary="[Admin] Statut courant Proxmox (current) - proxmox_vmid Horizon",
)
def admin_proxmox_status(proxmox_vmid: int, admin: AdminUser, db: Session = Depends(get_db)):
    return admin_service.admin_proxmox_vm_status(db, proxmox_vmid)


@router.get(
    "/proxmox/node-mappings",
    response_model=schemas.ProxmoxNodeMappingListResponse,
    summary="[Admin] Mappings nœud métier → Proxmox",
)
def list_node_mappings(admin: AdminUser, db: Session = Depends(get_db)):
    return admin_service.list_proxmox_node_mappings(db)


@router.post(
    "/proxmox/node-mappings",
    response_model=schemas.ProxmoxNodeMappingResponse,
    status_code=201,
    summary="[Admin] Créer un mapping nœud",
)
def create_node_mapping(
    body: schemas.ProxmoxNodeMappingCreate, admin: AdminUser, db: Session = Depends(get_db)
):
    return admin_service.create_proxmox_node_mapping(db, body)


@router.patch(
    "/proxmox/node-mappings/{mapping_id}",
    response_model=schemas.ProxmoxNodeMappingResponse,
    summary="[Admin] Mettre à jour un mapping nœud",
)
def patch_node_mapping(
    mapping_id: uuid.UUID,
    body: schemas.ProxmoxNodeMappingPatch,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    return admin_service.patch_proxmox_node_mapping(db, mapping_id, body)


@router.get(
    "/proxmox/iso-templates",
    response_model=schemas.IsoProxmoxTemplateListResponse,
    summary="[Admin] Correspondances ISO → template VMID",
)
def list_iso_templates(admin: AdminUser, db: Session = Depends(get_db)):
    return admin_service.list_iso_proxmox_templates(db)


@router.post(
    "/proxmox/iso-templates",
    response_model=schemas.IsoProxmoxTemplateResponse,
    status_code=201,
    summary="[Admin] Créer correspondance ISO → template",
)
def create_iso_template(
    body: schemas.IsoProxmoxTemplateCreate, admin: AdminUser, db: Session = Depends(get_db)
):
    return admin_service.create_iso_proxmox_template(db, body)


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
    return admin_service.patch_iso_proxmox_template(db, template_id, body)


@router.get(
    "/proxmox/summary",
    response_model=schemas.ProxmoxSummaryResponse,
    summary="[Admin] Résumé global du cluster Proxmox (Temps Réel)",
)
async def admin_proxmox_summary(admin: AdminUser):
    return await admin_service.get_proxmox_summary()


@router.get("/isos", response_model=schemas.ISOImageListResponse, summary="[Admin] Liste toutes les images ISO")
def admin_list_isos(admin: AdminUser, db: Session = Depends(get_db)):
    return admin_service.list_iso_images(db)


@router.post("/isos", response_model=schemas.ISOImageResponse, status_code=201, summary="[Admin] Ajouter une image ISO")
def admin_create_iso(body: schemas.ISOImageCreate, admin: AdminUser, db: Session = Depends(get_db)):
    return admin_service.create_iso_image(db, body)


@router.get(
    "/proxmox/storage-isos",
    summary="[Admin] Lister les fichiers ISO physiques sur Proxmox",
)
def admin_list_proxmox_isos(
    admin: AdminUser,
    node: str = Query("pve", description="Nœud Proxmox cible"),
    storage: str = Query("local", description="Nom du stockage Proxmox"),
):
    from horizon.infrastructure.proxmox_client import ProxmoxClient

    client = ProxmoxClient()
    return client.list_isos_on_storage(node, storage)


@router.post(
    "/proxmox/upload-iso",
    summary="[Admin] Uploader un fichier ISO physiquement vers Proxmox + enregistrement en DB",
)
async def admin_upload_proxmox_iso(
    admin: AdminUser,
    db: Session = Depends(get_db),
    node: str = Query("pve", description="Nœud Proxmox cible"),
    storage: str = Query("local", description="Stockage Proxmox destinataire"),
    name: str | None = Query(
        None,
        description="Nom convivial de l'ISO dans le catalogue (utilise le nom de fichier si absent)",
    ),
    os_family: str = Query(
        "LINUX",
        description="Famille OS : LINUX, WINDOWS, BSD, OTHER (insensible à la casse)",
    ),
    os_version: str = Query("Unknown", description="Version de l'OS (ex. Ubuntu 24.04)"),
    description: str | None = Query(None, description="Description libre de l'ISO"),
    # UploadFile doit être le dernier paramètre non-Query pour que FastAPI
    # parse correctement le multipart/form-data.
    file: UploadFile = File(..., description="Fichier ISO à uploader (.iso)"),
):
    """
    Upload multipart d'un fichier ISO :
    1. Réception du fichier via `UploadFile`.
    2. Upload physique vers le nœud Proxmox via `ProxmoxClient`.
    3. Enregistrement dans `iso_images` seulement si l'upload Proxmox réussit.
    """
    return await admin_service.upload_iso_to_proxmox(
        db=db,
        admin_id=admin.id,
        node=node,
        storage=storage,
        file_obj=file.file,
        filename=file.filename,
        name=name,
        os_family=os_family,
        os_version=os_version,
        description=description,
    )

@router.post(
    "/proxmox/tiny-vms",
    response_model=schemas.TinyVMResponse,
    status_code=201,
    summary="[Admin] Créer une TinyVM (micro-VM Alpine optimisée)",
    description=(
        "Crée une micro-VM aux ressources volontairement limitées (≤ 2 vCPUs, "
        "≤ 1 Go RAM, ≤ 10 Go disque) idéale pour des environnements de test ou "
        "des tâches légères. Utilise un ISO Alpine Linux par défaut. "
        "L'option `start_after_create` permet de démarrer la VM immédiatement."
    ),
)
async def admin_create_tiny_vm(
    body: schemas.TinyVMCreate,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Route dédiée aux TinyVMs.

    Le schéma `TinyVMCreate` plafonne les ressources côté validation Pydantic,
    ce qui rend cet endpoint visuellement distinct de `/proxmox/create-vm`
    dans la documentation Swagger.
    """
    return await admin_service.create_tiny_vm(db, body)


@router.post("/proxmox/create-vm", summary="[Admin] Créer une VM directement depuis un ISO (sans template)")
async def admin_create_proxmox_vm(
    body: schemas.ProxmoxCreateVMRequest, admin: AdminUser, db: Session = Depends(get_db)
):
    return await admin_service.create_vm_directly(db, body)


@router.post("/proxmox/prepare-template", summary="[Admin] Préparer une VM à partir d'un ISO pour en faire un template")

async def admin_prepare_template(
    body: schemas.PrepareTemplateRequest, admin: AdminUser, db: Session = Depends(get_db)
):
    return await admin_service.prepare_vm_template(db, body)


@router.get("/reservations", response_model=schemas.ReservationListResponse, summary="[Admin] Liste toutes les réservations")
def admin_list_reservations(admin: AdminUser, db: Session = Depends(get_db)):
    return admin_service.list_reservations(db)
