from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.api.deps import get_current_admin
from app.services.vm_service import VMService
from app.repositories.vm_repository import VMRepository
from app.repositories.infrastructure_repository import InfrastructureRepository
from app.repositories.audit_repository import AuditRepository
from app.infrastructure.proxmox import ProxmoxClient
from app.models.base_models import User
from app.schemas.vm import VMResponse

router = APIRouter()

async def get_vm_service(db: AsyncSession = Depends(get_db)):
    vm_repo = VMRepository(db)
    infra_repo = InfrastructureRepository(db)
    audit_repo = AuditRepository(db)
    proxmox = ProxmoxClient()
    return VMService(vm_repo, infra_repo, audit_repo, proxmox)

@router.get("/vms", response_model=List[VMResponse])
async def list_all_vms(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(get_current_admin),
    vm_service: VMService = Depends(get_vm_service)
):
    """Liste toutes les VMs du système (Admin seulement)."""
    res = await vm_service.vm_repo.list_all(skip=skip, limit=limit)
    return res

@router.post("/vms/{vm_id}/stop")
async def admin_stop_vm(
    vm_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    vm_service: VMService = Depends(get_vm_service)
):
    """Arrête une VM de force (Admin)."""
    await vm_service.stop_vm(vm_id, admin)
    return {"message": "VM stopped by admin"}

@router.get("/audit-logs")
async def list_audit_logs(
    limit: int = 100,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Récupère les logs d'audit système."""
    from sqlalchemy import select
    from app.models.base_models import AuditLog
    query = select(AuditLog).order_by(AuditLog.occurred_at.desc()).limit(limit)
    res = await db.execute(query)
    return res.scalars().all()

@router.get("/proxmox/summary")
async def get_proxmox_summary(
    admin: User = Depends(get_current_admin),
    vm_service: VMService = Depends(get_vm_service)
):
    """Résumé de l'état du cluster Proxmox."""
    # Simplified mock for now
    return {
        "status": "connected",
        "nodes": 1,
        "vms_total": await vm_service.vm_repo.count_all(),
    }
