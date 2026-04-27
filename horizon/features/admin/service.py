"""Logique métier réservée aux administrateurs."""

import logging
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

logger = logging.getLogger(__name__)


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
            "PROXMOX", "Proxmox est désactivé (PROXMOX_ENABLED=false).", 503)


def assert_known_proxmox_node_name(db: Session, node_name: str) -> None:
    known = {r.proxmox_node_name for r in db.query(ProxmoxNodeMapping).all()}
    if node_name not in known:
        raise PolicyError(
            "PROXMOX",
            f"Nœud Proxmox inconnu ou non mappé : {node_name}",
            400,
        )


def admin_proxmox_pause_by_vmid(db: Session, proxmox_vmid: int) -> schemas.ProxmoxOperationResponse:
    from horizon.infrastructure.proxmox_client import ProxmoxClient, ProxmoxIntegrationError

    _require_proxmox_enabled()
    vm = db.query(VirtualMachine).filter(
        VirtualMachine.proxmox_vmid == proxmox_vmid).first()
    if not vm:
        raise PolicyError("VM", "Aucune VM Horizon avec ce proxmox_vmid.", 404)
    px_node = _resolve_proxmox_node_name(db, vm.node)
    try:
        client = ProxmoxClient()
        out = client.pause_vm(px_node, proxmox_vmid)
    except ProxmoxIntegrationError as e:
        raise PolicyError("PROXMOX", e.message, e.status_code) from e
    return schemas.ProxmoxOperationResponse(status=out["status"], message=out["message"])


def admin_proxmox_list_qemu(db: Session, node_name: str) -> schemas.ProxmoxQemuListResponse:
    from horizon.infrastructure.proxmox_client import ProxmoxClient, ProxmoxIntegrationError

    _require_proxmox_enabled()
    assert_known_proxmox_node_name(db, node_name)
    try:
        client = ProxmoxClient()
        vms = client.list_node_qemu(node_name)
    except ProxmoxIntegrationError as e:
        raise PolicyError("PROXMOX", e.message, e.status_code) from e
    return schemas.ProxmoxQemuListResponse(count=len(vms), items=vms)


def admin_proxmox_vm_status(db: Session, proxmox_vmid: int) -> schemas.ProxmoxVmStatusResponse:
    from horizon.infrastructure.proxmox_client import ProxmoxClient, ProxmoxIntegrationError

    _require_proxmox_enabled()
    vm = db.query(VirtualMachine).filter(
        VirtualMachine.proxmox_vmid == proxmox_vmid).first()
    if not vm:
        raise PolicyError("VM", "Aucune VM Horizon avec ce proxmox_vmid.", 404)
    px_node = _resolve_proxmox_node_name(db, vm.node)
    try:
        client = ProxmoxClient()
        data = client.get_vm_current_status(px_node, proxmox_vmid)
    except ProxmoxIntegrationError as e:
        raise PolicyError("PROXMOX", e.message, e.status_code) from e
    return schemas.ProxmoxVmStatusResponse(data=data)


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
                duration_hours=int((r.end_time - r.start_time).total_seconds() // 3600),
                status=vm.status.value if vm else "TERMINÉE",
                created_at=r.created_at,
            )
        )
    return schemas.ReservationListResponse(items=items)


def list_proxmox_node_mappings(db: Session) -> schemas.ProxmoxNodeMappingListResponse:
    rows = db.query(ProxmoxNodeMapping).order_by(
        ProxmoxNodeMapping.physical_node).all()
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
            "PROXMOX", "physical_node doit être REM, RAM ou EMILIA.", 422) from e
    if db.query(ProxmoxNodeMapping).filter(ProxmoxNodeMapping.physical_node == pn).first():
        raise PolicyError(
            "PROXMOX", "Un mapping existe déjà pour ce nœud métier.", 409)
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
        ProxmoxNodeMapping.id == mapping_id).first()
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
    if db.query(IsoProxmoxTemplate).filter(IsoProxmoxTemplate.iso_image_id == body.iso_image_id).first():
        raise PolicyError(
            "PROXMOX", "Un template existe déjà pour cette ISO.", 409)
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
        IsoProxmoxTemplate.id == template_id).first()
    if not row:
        raise PolicyError(
            "PROXMOX", "Correspondance ISO-template introuvable.", 404)
    row.proxmox_template_vmid = body.proxmox_template_vmid
    db.commit()
    db.refresh(row)
    res = schemas.IsoProxmoxTemplateResponse.model_validate(row)
    res.iso_name = row.iso_image.name if row.iso_image else "Inconnu"
    return res


def list_iso_images(db: Session) -> schemas.ISOImageListResponse:
    rows = db.query(ISOImage).order_by(ISOImage.created_at.desc()).all()
    return schemas.ISOImageListResponse(
        items=[schemas.ISOImageResponse.model_validate(r) for r in rows]
    )


def create_iso_image(db: Session, body: schemas.ISOImageCreate) -> schemas.ISOImageResponse:
    row = ISOImage(
        id=uuid.uuid4(),
        **body.model_dump()
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return schemas.ISOImageResponse.model_validate(row)


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


async def check_proxmox_health() -> schemas.ProxmoxHealthResponse:
    from horizon.infrastructure.proxmox_client import (
        ProxmoxClient,
        ProxmoxIntegrationError,
    )

    if not get_settings().PROXMOX_ENABLED:
        return schemas.ProxmoxHealthResponse(online=False, nodes_up=0, nodes_total=0)

    try:
        client = ProxmoxClient()
        # On utilise un appel léger pour vérifier la santé
        nodes = client.api.nodes.get()
        nodes_up = sum(1 for n in nodes if n.get("status") == "online")
        return schemas.ProxmoxHealthResponse(
            online=nodes_up > 0,
            nodes_up=nodes_up,
            nodes_total=len(nodes)
        )
    except Exception:
        return schemas.ProxmoxHealthResponse(online=False, nodes_up=0, nodes_total=0)


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
    from horizon.infrastructure.proxmox_client import (
        ProxmoxClient,
        ProxmoxIntegrationError,
    )

    _require_proxmox_enabled()
    os_family = os_family.upper()
    try:
        client = ProxmoxClient()
        # 1. Upload physique vers Proxmox
        res = await client.upload_iso(node, storage, file_obj, filename)

        # 2. Enregistrement automatique dans la table iso_images
        new_iso = ISOImage(
            id=uuid.uuid4(),
            name=name or filename,
            filename=filename,
            os_family=os_family,
            os_version=os_version,
            description=description,
            added_by_id=admin_id,
            is_active=True
        )
        db.add(new_iso)
        db.commit()
        db.refresh(new_iso)

        res["iso_id"] = str(new_iso.id)
        res["database_status"] = "registered"
        return res
    except ProxmoxIntegrationError as e:
        raise PolicyError("PROXMOX", e.message, e.status_code) from e


async def prepare_vm_template(db: Session, body: schemas.PrepareTemplateRequest) -> dict[str, Any]:
    from horizon.infrastructure.proxmox_client import (
        ProxmoxClient,
        ProxmoxIntegrationError,
    )
    
    _require_proxmox_enabled()
    try:
        client = ProxmoxClient()
        # On prépare la VM sur Proxmox
        res = await client.prepare_vm_for_template(
            node=body.node,
            vmid=body.vmid,
            storage=body.storage,
            iso_filename=body.iso_filename,
            name=body.name,
            vcpu=body.vcpu,
            ram_mb=body.ram_mb,
            storage_gb=body.storage_gb,
            iso_storage=body.iso_storage
        )
        
        # On enregistre automatiquement le template dans la base de données
        # On cherche l'ISO correspondante par son nom de fichier
        iso = db.query(ISOImage).filter(ISOImage.filename == body.iso_filename).first()
        if iso:
            # Vérifier si un mapping existe déjà pour cet ISO (on le met à jour ou on ignore)
            existing_template = db.query(IsoProxmoxTemplate).filter(IsoProxmoxTemplate.iso_image_id == iso.id).first()
            if existing_template:
                existing_template.proxmox_template_vmid = body.vmid
            else:
                new_template = IsoProxmoxTemplate(
                    iso_image_id=iso.id,
                    proxmox_template_vmid=body.vmid
                )
                db.add(new_template)
            
            db.commit()
            logger.info(f"Template auto-enregistré : ISO {iso.name} -> VMID {body.vmid}")
        else:
            logger.warning(f"Impossible d'auto-enregistrer le template : ISO {body.iso_filename} non trouvée en base.")
            
        return res
    except ProxmoxIntegrationError as e:
        raise PolicyError("PROXMOX", e.message, e.status_code) from e


async def create_vm_directly(db: Session, body: schemas.ProxmoxCreateVMRequest) -> dict[str, Any]:
    from horizon.infrastructure.proxmox_client import ProxmoxClient, ProxmoxIntegrationError
    from datetime import datetime, timezone, timedelta
    from horizon.shared.models import VirtualMachine, Reservation, ISOImage, ProxmoxNodeMapping
    from horizon.shared.models.virtual_machine import PhysicalNode, VMStatus
    import uuid as _uuid

    _require_proxmox_enabled()

    if not body.owner_id:
        raise PolicyError("VM", "owner_id is required to register VM in database.", 422)

    now = datetime.now(timezone.utc)

    # Resolve physical node
    mapping = db.query(ProxmoxNodeMapping).filter(
        ProxmoxNodeMapping.proxmox_node_name == body.node
    ).first()
    physical_node = mapping.physical_node if mapping else PhysicalNode.REM

    # Try to link ISO by filename
    iso = db.query(ISOImage).filter(ISOImage.filename == body.iso_filename).first()
    iso_id = iso.id if iso else None

    # Stage the VM record before touching Proxmox
    vm = VirtualMachine(
        id=_uuid.uuid4(),
        proxmox_vmid=body.vmid,
        name=body.name,
        description=None,
        owner_id=_uuid.UUID(body.owner_id),
        node=physical_node,
        vcpu=body.vcpu,
        ram_gb=round(float(body.ram_mb) / 1024.0, 3),
        storage_gb=body.storage_gb,
        iso_image_id=iso_id,
        status=VMStatus.PENDING,
        lease_start=now,
        lease_end=now + timedelta(hours=body.session_hours),
        vlan_id=None,
        ip_address=None,
        ssh_public_key=body.ssh_public_key,
        shared_space_gb=0.0,
    )
    db.add(vm)

    reservation = Reservation(
        id=_uuid.uuid4(),
        vm_id=vm.id,
        user_id=_uuid.UUID(body.owner_id),
        start_time=vm.lease_start,
        end_time=vm.lease_end,
    )
    db.add(reservation)

    try:
        db.flush()  # Validate constraints before hitting Proxmox

        try:
            client = ProxmoxClient()
        except ProxmoxIntegrationError as e:
            raise PolicyError("PROXMOX", e.message, e.status_code) from e

        try:
            res = await client.create_vm(
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
                ssh_key=body.ssh_public_key,
            )
            await client.start_vm(node=body.node, vmid=body.vmid)
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
            },
        }
    except PolicyError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
