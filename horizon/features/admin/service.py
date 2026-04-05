"""Logique métier réservée aux administrateurs."""

import uuid

from sqlalchemy.orm import Session

from horizon.core.config import get_settings
from horizon.features.admin import schemas
from horizon.features.vms import service as vm_service
from horizon.features.vms.service import _resolve_proxmox_node_name
from horizon.shared.models import (
    IsoProxmoxTemplate,
    ProxmoxNodeMapping,
    QuotaOverride,
    User,
    VirtualMachine,
)
from horizon.shared.models.virtual_machine import PhysicalNode
from horizon.shared.policies.enforcer import PolicyError


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
    return schemas.IsoProxmoxTemplateListResponse(
        items=[schemas.IsoProxmoxTemplateResponse.model_validate(
            r) for r in rows]
    )


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
    return schemas.IsoProxmoxTemplateResponse.model_validate(row)


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
    return schemas.IsoProxmoxTemplateResponse.model_validate(row)
