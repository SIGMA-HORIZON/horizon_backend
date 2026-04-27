"""Logique métier réservée aux administrateurs."""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from horizon.core.config import get_settings
from horizon.features.admin import schemas
from horizon.features.vms import service as vm_service
from horizon.features.vms.service import _resolve_proxmox_node_name
from horizon.shared.models import (
    ISOImage,
    IsoProxmoxTemplate,
    ProxmoxNodeMapping,
    QuotaOverride,
    Reservation,
    User,
    VirtualMachine,
)
from horizon.shared.models.virtual_machine import PhysicalNode
from horizon.shared.policies.enforcer import PolicyError


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------


def build_admin_vm_dashboard(db: Session) -> schemas.AdminVMListResponse:
    vms = vm_service.get_all_vms_admin(db)
    items: list[schemas.AdminVMRowResponse] = []
    for vm in vms:
        owner = db.query(User).filter(User.id == vm.owner_id).first()
        items.append(
            schemas.AdminVMRowResponse(
                id=vm.id,
                proxmox_vmid=vm.proxmox_vmid,
                name=vm.name,
                owner_username=owner.username if owner else None,
                node=vm.node.value,
                vcpu=vm.vcpu,
                ram_gb=vm.ram_gb,
                storage_gb=vm.storage_gb,
                status=vm.status.value,
                lease_end=vm.lease_end,
                ip_address=vm.ip_address,
            )
        )
    return schemas.AdminVMListResponse(items=items)


def apply_quota_override(db: Session, body: schemas.QuotaOverrideRequest, admin_id) -> None:
    data = body.model_dump(exclude={"user_id", "reason"}, exclude_none=True)

    existing = (
        db.query(QuotaOverride)
        .filter(QuotaOverride.user_id == uuid.UUID(body.user_id))
        .first()
    )

    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        existing.granted_by_id = admin_id
        existing.reason = body.reason
    else:
        override = QuotaOverride(
            id=uuid.uuid4(),
            user_id=uuid.UUID(body.user_id),
            granted_by_id=admin_id,
            reason=body.reason,
            **data,
        )
        db.add(override)


def get_vm_or_404(db: Session, vm_id: uuid.UUID) -> VirtualMachine:
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise PolicyError("VM", "VM introuvable.", 404)
    return vm


def _require_proxmox_enabled() -> None:
    if not get_settings().PROXMOX_ENABLED:
        raise PolicyError(
            "PROXMOX", "Proxmox est désactivé (PROXMOX_ENABLED=false).", 503
        )


def assert_known_proxmox_node_name(db: Session, node_name: str) -> None:
    known = {r.proxmox_node_name for r in db.query(ProxmoxNodeMapping).all()}
    if node_name not in known:
        raise PolicyError(
            "PROXMOX",
            f"Nœud Proxmox inconnu ou non mappé : {node_name}",
            400,
        )


# ---------------------------------------------------------------------------
# Opérations Proxmox (Pause / Liste QEMU / Statut)
# ---------------------------------------------------------------------------


def admin_proxmox_pause_by_vmid(
    db: Session, proxmox_vmid: int
) -> schemas.ProxmoxOperationResponse:
    from horizon.infrastructure.proxmox_client import ProxmoxClient, ProxmoxIntegrationError

    _require_proxmox_enabled()
    vm = db.query(VirtualMachine).filter(
        VirtualMachine.proxmox_vmid == proxmox_vmid
    ).first()
    if not vm:
        raise PolicyError("VM", "Aucune VM Horizon avec ce proxmox_vmid.", 404)
    px_node = _resolve_proxmox_node_name(db, vm.node)
    try:
        client = ProxmoxClient()
        out = client.pause_vm(px_node, proxmox_vmid)
    except ProxmoxIntegrationError as e:
        raise PolicyError("PROXMOX", e.message, e.status_code) from e
    return schemas.ProxmoxOperationResponse(status=out["status"], message=out["message"])


def admin_proxmox_list_qemu(
    db: Session, node_name: str
) -> schemas.ProxmoxQemuListResponse:
    from horizon.infrastructure.proxmox_client import ProxmoxClient, ProxmoxIntegrationError

    _require_proxmox_enabled()
    assert_known_proxmox_node_name(db, node_name)
    try:
        client = ProxmoxClient()
        vms = client.list_node_qemu(node_name)
    except ProxmoxIntegrationError as e:
        raise PolicyError("PROXMOX", e.message, e.status_code) from e
    return schemas.ProxmoxQemuListResponse(count=len(vms), items=vms)


def admin_proxmox_vm_status(
    db: Session, proxmox_vmid: int
) -> schemas.ProxmoxVmStatusResponse:
    from horizon.infrastructure.proxmox_client import ProxmoxClient, ProxmoxIntegrationError

    _require_proxmox_enabled()
    vm = db.query(VirtualMachine).filter(
        VirtualMachine.proxmox_vmid == proxmox_vmid
    ).first()
    if not vm:
        raise PolicyError("VM", "Aucune VM Horizon avec ce proxmox_vmid.", 404)
    px_node = _resolve_proxmox_node_name(db, vm.node)
    try:
        client = ProxmoxClient()
        data = client.get_vm_current_status(px_node, proxmox_vmid)
    except ProxmoxIntegrationError as e:
        raise PolicyError("PROXMOX", e.message, e.status_code) from e
    return schemas.ProxmoxVmStatusResponse(data=data)


# ---------------------------------------------------------------------------
# Réservations
# ---------------------------------------------------------------------------


def list_reservations(db: Session) -> schemas.ReservationListResponse:
    rows = db.query(Reservation).order_by(Reservation.created_at.desc()).all()
    items = []
    for r in rows:
        vm = r.vm
        user = r.user
        items.append(
            schemas.ReservationRowResponse(
                id=r.id,
                vm_name=vm.name if vm else "VM inconnue",
                user_full_name=f"{user.first_name} {user.last_name}" if user else "Inconnu",
                user_email=user.email if user else "-",
                os_name=vm.iso_image.name if (vm and vm.iso_image) else "N/A",
                vcpu=vm.vcpu if vm else 0,
                ram_gb=vm.ram_gb if vm else 0.0,
                storage_gb=vm.storage_gb if vm else 0.0,
                duration_hours=int(
                    (r.end_time - r.start_time).total_seconds() // 3600
                ),
                status=vm.status.value if vm else "TERMINÉE",
                created_at=r.created_at,
            )
        )
    return schemas.ReservationListResponse(items=items)


# ---------------------------------------------------------------------------
# Mappings nœud physique ↔ Proxmox
# ---------------------------------------------------------------------------


def list_proxmox_node_mappings(db: Session) -> schemas.ProxmoxNodeMappingListResponse:
    rows = db.query(ProxmoxNodeMapping).order_by(
        ProxmoxNodeMapping.physical_node
    ).all()
    return schemas.ProxmoxNodeMappingListResponse(
        items=[
            schemas.ProxmoxNodeMappingResponse(
                id=r.id,
                physical_node=r.physical_node.value,
                proxmox_node_name=r.proxmox_node_name,
            )
            for r in rows
        ]
    )


def create_proxmox_node_mapping(
    db: Session, body: schemas.ProxmoxNodeMappingCreate
) -> schemas.ProxmoxNodeMappingResponse:
    try:
        pn = PhysicalNode(body.physical_node.upper())
    except ValueError as e:
        raise PolicyError(
            "PROXMOX", "physical_node doit être REM, RAM ou EMILIA.", 422
        ) from e
    if db.query(ProxmoxNodeMapping).filter(
        ProxmoxNodeMapping.physical_node == pn
    ).first():
        raise PolicyError(
            "PROXMOX", "Un mapping existe déjà pour ce nœud métier.", 409
        )
    row = ProxmoxNodeMapping(
        id=uuid.uuid4(),
        physical_node=pn,
        proxmox_node_name=body.proxmox_node_name,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return schemas.ProxmoxNodeMappingResponse(
        id=row.id,
        physical_node=row.physical_node.value,
        proxmox_node_name=row.proxmox_node_name,
    )


def patch_proxmox_node_mapping(
    db: Session, mapping_id: uuid.UUID, body: schemas.ProxmoxNodeMappingPatch
) -> schemas.ProxmoxNodeMappingResponse:
    row = db.query(ProxmoxNodeMapping).filter(
        ProxmoxNodeMapping.id == mapping_id
    ).first()
    if not row:
        raise PolicyError("PROXMOX", "Mapping introuvable.", 404)
    row.proxmox_node_name = body.proxmox_node_name
    db.commit()
    db.refresh(row)
    return schemas.ProxmoxNodeMappingResponse(
        id=row.id,
        physical_node=row.physical_node.value,
        proxmox_node_name=row.proxmox_node_name,
    )


# ---------------------------------------------------------------------------
# ISO ↔ template VMID
# ---------------------------------------------------------------------------


def list_iso_proxmox_templates(db: Session) -> schemas.IsoProxmoxTemplateListResponse:
    rows = db.query(IsoProxmoxTemplate).all()
    items = []
    for r in rows:
        item = schemas.IsoProxmoxTemplateResponse.model_validate(r)
        item.iso_name = r.iso_image.name if r.iso_image else "Inconnu"
        items.append(item)
    return schemas.IsoProxmoxTemplateListResponse(items=items)


def create_iso_proxmox_template(
    db: Session, body: schemas.IsoProxmoxTemplateCreate
) -> schemas.IsoProxmoxTemplateResponse:
    if db.query(IsoProxmoxTemplate).filter(
        IsoProxmoxTemplate.iso_image_id == body.iso_image_id
    ).first():
        raise PolicyError(
            "PROXMOX", "Un template existe déjà pour cette ISO.", 409
        )
    row = IsoProxmoxTemplate(
        id=uuid.uuid4(),
        iso_image_id=body.iso_image_id,
        proxmox_template_vmid=body.proxmox_template_vmid,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    res = schemas.IsoProxmoxTemplateResponse.model_validate(row)
    res.iso_name = row.iso_image.name if row.iso_image else "Inconnu"
    return res


def patch_iso_proxmox_template(
    db: Session, template_id: uuid.UUID, body: schemas.IsoProxmoxTemplatePatch
) -> schemas.IsoProxmoxTemplateResponse:
    row = db.query(IsoProxmoxTemplate).filter(
        IsoProxmoxTemplate.id == template_id
    ).first()
    if not row:
        raise PolicyError(
            "PROXMOX", "Correspondance ISO-template introuvable.", 404
        )
    row.proxmox_template_vmid = body.proxmox_template_vmid
    db.commit()
    db.refresh(row)
    res = schemas.IsoProxmoxTemplateResponse.model_validate(row)
    res.iso_name = row.iso_image.name if row.iso_image else "Inconnu"
    return res


# ---------------------------------------------------------------------------
# Images ISO (table iso_images)
# ---------------------------------------------------------------------------


def list_iso_images(db: Session) -> schemas.ISOImageListResponse:
    rows = db.query(ISOImage).order_by(ISOImage.created_at.desc()).all()
    return schemas.ISOImageListResponse(
        items=[schemas.ISOImageResponse.model_validate(r) for r in rows]
    )


def create_iso_image(
    db: Session, body: schemas.ISOImageCreate
) -> schemas.ISOImageResponse:
    """
    Enregistre une image ISO en base de données (entrée manuelle, sans upload physique).

    La normalisation en majuscule de `os_family` est déléguée au validator
    Pydantic de `ISOImageCreate`, ce qui garantit qu'aucun doublon de casse
    ne peut atteindre la colonne `os_family_enum`.
    """
    row = ISOImage(
        id=uuid.uuid4(),
        **body.model_dump(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return schemas.ISOImageResponse.model_validate(row)


# ---------------------------------------------------------------------------
# Résumé global du cluster Proxmox
# ---------------------------------------------------------------------------


async def get_proxmox_summary() -> schemas.ProxmoxSummaryResponse:
    from horizon.infrastructure.proxmox_client import (
        ProxmoxClient,
        ProxmoxIntegrationError,
    )

    _require_proxmox_enabled()
    try:
        client = ProxmoxClient()
        data = client.get_cluster_status()
        return schemas.ProxmoxSummaryResponse(**data)
    except ProxmoxIntegrationError as e:
        raise PolicyError("PROXMOX", e.message, e.status_code) from e


# ---------------------------------------------------------------------------
# Upload physique d'ISO vers Proxmox + enregistrement en DB
# ---------------------------------------------------------------------------


async def upload_iso_to_proxmox(
    db: Session,
    admin_id: uuid.UUID,
    node: str,
    storage: str,
    file_obj,
    filename: str,
    name: str | None = None,
    os_family: str = "LINUX",
    os_version: str = "Unknown",
    description: str | None = None,
) -> dict[str, Any]:
    """
    Réceptionne un fichier ISO (UploadFile.file), l'uploade physiquement sur le
    nœud Proxmox via ProxmoxClient, puis — seulement en cas de succès — crée
    l'entrée correspondante dans la table iso_images.

    Garanties :
    - `os_family` est toujours converti en majuscule avant l'insertion pour
      éviter l'erreur « invalid input value for enum os_family_enum ».
    - L'entrée en DB n'est jamais créée si l'upload Proxmox échoue.
    """
    from horizon.infrastructure.proxmox_client import (
        ProxmoxClient,
        ProxmoxIntegrationError,
    )

    _require_proxmox_enabled()

    # Normalisation os_family — défense en profondeur même si le validator
    # Pydantic n'est pas passé par là (appel direct depuis un autre service).
    os_family_normalised = os_family.upper()

    try:
        client = ProxmoxClient()

        # --- Étape 1 : upload physique vers Proxmox ---
        # ProxmoxClient.upload_iso attend un file-like object binaire et le nom
        # du fichier. On lit les bytes ici pour compatibilité avec proxmoxer qui
        # n'accepte pas toujours les streams non seekables.
        file_bytes: bytes = file_obj.read()
        proxmox_result = await client.upload_iso(
            node=node,
            storage=storage,
            file_content=file_bytes,
            filename=filename,
        )

        # --- Étape 2 : enregistrement en DB (seulement si upload réussi) ---
        new_iso = ISOImage(
            id=uuid.uuid4(),
            name=name or filename,
            filename=filename,
            os_family=os_family_normalised,
            os_version=os_version,
            description=description,
            added_by_id=admin_id,
            is_active=True,
        )
        db.add(new_iso)
        db.commit()
        db.refresh(new_iso)

        proxmox_result["iso_id"] = str(new_iso.id)
        proxmox_result["database_status"] = "registered"
        return proxmox_result

    except ProxmoxIntegrationError as e:
        # L'upload a échoué : on ne touche pas la DB.
        raise PolicyError("PROXMOX", e.message, e.status_code) from e


# ---------------------------------------------------------------------------
# Préparation de template VM
# ---------------------------------------------------------------------------


async def prepare_vm_template(
    db: Session, body: schemas.PrepareTemplateRequest
) -> dict[str, Any]:
    from horizon.infrastructure.proxmox_client import (
        ProxmoxClient,
        ProxmoxIntegrationError,
    )

    _require_proxmox_enabled()
    try:
        client = ProxmoxClient()
        return await client.prepare_vm_for_template(
            node=body.node,
            vmid=body.vmid,
            storage=body.storage,
            iso_filename=body.iso_filename,
            name=body.name,
            vcpu=body.vcpu,
            ram_mb=body.ram_mb,
            storage_gb=body.storage_gb,
            iso_storage=body.iso_storage,
        )
    except ProxmoxIntegrationError as e:
        raise PolicyError("PROXMOX", e.message, e.status_code) from e


# ---------------------------------------------------------------------------
# Création directe de VM
# ---------------------------------------------------------------------------


async def create_vm_directly(
    db: Session, body: schemas.ProxmoxCreateVMRequest
) -> dict[str, Any]:
    from horizon.infrastructure.proxmox_client import (
        ProxmoxClient,
        ProxmoxIntegrationError,
    )

    _require_proxmox_enabled()
    try:
        client = ProxmoxClient()
        return await client.create_vm(
            node=body.node,
            vmid=body.vmid,
            name=body.name,
            storage=body.storage,
            iso_filename=body.iso_filename,
            vcpu=body.vcpu,
            ram_mb=body.ram_mb,
            storage_gb=body.storage_gb,
            iso_storage=body.iso_storage,
            net0=body.net0,
        )
    except ProxmoxIntegrationError as e:
        raise PolicyError("PROXMOX", e.message, e.status_code) from e


# ---------------------------------------------------------------------------
# TinyVM — micro-VMs optimisées (Alpine Linux)
# ---------------------------------------------------------------------------


async def create_tiny_vm(
    db: Session,
    body: schemas.TinyVMCreate,
) -> schemas.TinyVMResponse:
    """
    Crée une TinyVM (micro-VM Alpine) sur Proxmox.

    Flux :
    1. Appel ProxmoxClient.create_vm avec les paramètres restreints du schéma.
    2. Si `start_after_create=True`, appel ProxmoxClient.start_vm.
    3. Retourne un TinyVMResponse structuré.

    Contraintes respectées :
    - Séparation stricte Route → Service → ProxmoxClient.
    - Aucune logique Proxmox dans la couche router.
    - os_family non concerné ici (pas d'insertion ISO en DB).
    """
    from horizon.infrastructure.proxmox_client import (
        ProxmoxClient,
        ProxmoxIntegrationError,
    )

    _require_proxmox_enabled()

    try:
        client = ProxmoxClient()

        # --- Étape 1 : création de la VM ---
        create_result = await client.create_vm(
            node=body.node,
            vmid=body.vmid,
            name=body.name,
            storage=body.storage,
            iso_filename=body.iso_filename,
            vcpu=body.vcpu,
            ram_mb=body.ram_mb,
            storage_gb=body.storage_gb,
            iso_storage=body.iso_storage,
            net0=body.net0,
        )

        start_result: dict[str, Any] | None = None
        final_status = "stopped"

        # --- Étape 2 (optionnelle) : démarrage immédiat ---
        if body.start_after_create:
            start_result = await client.start_vm(node=body.node, vmid=body.vmid)
            final_status = "running"

        return schemas.TinyVMResponse(
            vmid=body.vmid,
            node=body.node,
            name=body.name,
            status=final_status,
            message=(
                f"TinyVM '{body.name}' (VMID {body.vmid}) créée avec succès"
                + (" et démarrée." if body.start_after_create else ".")
            ),
            proxmox_task={
                "create": create_result,
                "start": start_result,
            },
        )

    except ProxmoxIntegrationError as e:
        raise PolicyError("PROXMOX", e.message, e.status_code) from e