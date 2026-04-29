from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.api.deps import get_current_user
from app.schemas.vm import VMCreate, VMResponse, VMListResponse, ClusterStatusResponse, ISOResponse
from app.services.vm_service import VMService
from app.repositories.vm_repository import VMRepository
from app.repositories.infrastructure_repository import InfrastructureRepository
from app.repositories.audit_repository import AuditRepository
from app.infrastructure.proxmox import ProxmoxClient
from app.models.base_models import User

router = APIRouter()

async def get_vm_service(db: AsyncSession = Depends(get_db)):
    vm_repo = VMRepository(db)
    infra_repo = InfrastructureRepository(db)
    audit_repo = AuditRepository(db)
    proxmox = ProxmoxClient()
    return VMService(vm_repo, infra_repo, audit_repo, proxmox)

@router.get("/", response_model=VMListResponse)
async def list_vms(
    current_user: User = Depends(get_current_user),
    vm_service: VMService = Depends(get_vm_service)
):
    """Liste toutes les machines virtuelles de l'utilisateur connecté."""
    return await vm_service.list_user_vms(current_user)

@router.post("/", response_model=VMResponse, status_code=status.HTTP_201_CREATED)
async def create_vm(
    request: Request,
    vm_in: VMCreate,
    current_user: User = Depends(get_current_user),
    vm_service: VMService = Depends(get_vm_service)
):
    """Crée une nouvelle machine virtuelle."""
    ip_address = request.client.host if request.client else "0.0.0.0"
    return await vm_service.create_vm(current_user, vm_in, ip_address)


@router.get("/available-isos", response_model=List[ISOResponse])
async def list_available_isos(
    db: AsyncSession = Depends(get_db)
):
    """Liste les images ISO disponibles pour la création de VM."""
    infra_repo = InfrastructureRepository(db)
    return await infra_repo.list_isos()

@router.get("/cluster/status")
async def get_cluster_status(
    vm_service: VMService = Depends(get_vm_service)
):
    """Obtient le statut global du cluster (CPU/RAM)."""
    # Version simplifiée pour le moment
    return {
        "nodes": [{"hostname": "pve", "status": "online"}],
        "total_cpu": 32,
        "used_cpu": 0,
        "total_ram": 128,
        "used_ram": 0
    }

@router.get("/{vm_id}", response_model=VMResponse)
async def get_vm(
    vm_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    vm_service: VMService = Depends(get_vm_service)
):
    """Récupère les détails d'une VM spécifique."""
    return await vm_service.get_vm(vm_id, current_user)

@router.post("/{vm_id}/start")
async def start_vm(
    vm_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    vm_service: VMService = Depends(get_vm_service)
):
    """Démarre une VM."""
    await vm_service.start_vm(vm_id, current_user)
    return {"message": "VM started successfully"}

@router.post("/{vm_id}/stop")
async def stop_vm(
    vm_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    vm_service: VMService = Depends(get_vm_service)
):
    """Arrête une VM."""
    await vm_service.stop_vm(vm_id, current_user)
    return {"message": "VM stopped successfully"}

@router.delete("/{vm_id}")
async def delete_vm(
    vm_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    vm_service: VMService = Depends(get_vm_service)
):
    """Supprime une VM."""
    await vm_service.delete_vm(vm_id, current_user)
    return {"message": "VM deleted successfully"}
