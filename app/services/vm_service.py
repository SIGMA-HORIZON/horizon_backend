from datetime import datetime, timedelta
import uuid
import logging
from typing import List, Optional, Dict, Any

from app.repositories.vm_repository import VMRepository
from app.repositories.infrastructure_repository import InfrastructureRepository
from app.repositories.audit_repository import AuditRepository
from app.infrastructure.proxmox import ProxmoxClient
from app.models.base_models import VirtualMachine, User, PhysicalNode, ISOImage, SSHKey
from app.models.enums import VMStatus, ActionType, SSHAlgorithm
from app.schemas.vm import VMCreate, VMUpdate

logger = logging.getLogger(__name__)

class VMService:
    def __init__(
        self, 
        vm_repo: VMRepository, 
        infra_repo: InfrastructureRepository, 
        audit_repo: AuditRepository, 
        proxmox: ProxmoxClient
    ):
        self.vm_repo = vm_repo
        self.infra_repo = infra_repo
        self.audit_repo = audit_repo
        self.proxmox = proxmox

    async def list_user_vms(self, user: User) -> Dict[str, Any]:
        vms = await self.vm_repo.list_by_user(user.id)
        return {"items": vms, "total": len(vms)}

    async def get_vm(self, vm_id: uuid.UUID, user: User) -> VirtualMachine:
        vm = await self.vm_repo.get(vm_id)
        if not vm or (vm.user_id != user.id and user.role.role_type != "admin"):
            raise Exception("Virtual Machine not found")
        return vm

    async def create_vm(self, user: User, vm_in: VMCreate, ip_address: str) -> VirtualMachine:
        # 1. Validation de l'ISO
        iso = await self.infra_repo.get_iso(vm_in.iso_image_id)
        if not iso:
            raise Exception("Image ISO introuvable ou inactive")

        # 2. Validation des ressources (Schéma Quota à implémenter ultérieurement)
        # TODO: Vérifier les quotas de l'utilisateur

        # 3. Sélection du Node (PVE par défaut pour le moment)
        nodes = await self.infra_repo.get_active_nodes()
        if not nodes:
            raise Exception("Aucun noeud physique disponible")
        node = nodes[0]

        # 4. Préparation de l'entrée DB
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=vm_in.duration_hours)
        
        # Génération d'un VMID unique pour Proxmox (simulation)
        # Dans un vrai système, on interrogerait le cluster pour le prochain ID libre
        vm_count = await self.vm_repo.count_all()
        new_vmid = 1000 + vm_count

        # Création de la clé SSH si fournie
        ssh_key = None
        if vm_in.ssh_public_key:
            ssh_key = SSHKey(
                public_key=vm_in.ssh_public_key,
                algorithm=SSHAlgorithm.ED25519 # Par défaut
            )
            self.vm_repo.db.add(ssh_key)
            await self.vm_repo.db.flush()

        # Récupération de la politique par défaut
        from sqlalchemy import select
        from app.models.base_models import UsagePolicy
        res = await self.vm_repo.db.execute(select(UsagePolicy).where(UsagePolicy.is_default == True))
        policy = res.scalars().first()
        if not policy:
             raise Exception("Aucune politique d'utilisation par défaut configurée")

        vm = VirtualMachine(
            user_id=user.id,
            policy_id=policy.id,
            node_id=node.id,
            iso_image_id=iso.id,
            ssh_key_id=ssh_key.id if ssh_key else None,
            name=vm_in.name,
            proxmox_vmid=new_vmid,
            status=VMStatus.PROVISIONING,
            cpu_cores=vm_in.cpu_cores,
            ram_gb=vm_in.ram_gb,
            disk_gb=vm_in.disk_gb,
            duration_hours=vm_in.duration_hours,
            start_time=start_time,
            end_time=end_time
        )

        await self.vm_repo.create(vm)

        # 5. Appel à Proxmox (Async en tâche de fond idéalement)
        if self.proxmox.enabled:
            try:
                # Simulation de création via Proxmox Client
                # logger.info(f"Appel Proxmox pour VM {vm.name} (ID: {new_vmid})")
                # self.proxmox.create_vm_from_template(...)
                vm.status = VMStatus.RUNNING # Changement direct pour le dev
                await self.vm_repo.db.commit()
            except Exception as e:
                logger.error(f"Erreur Proxmox: {e}")
                vm.status = VMStatus.FAILED
                await self.vm_repo.db.commit()
        else:
            vm.status = VMStatus.RUNNING # Mocked
            await self.vm_repo.db.commit()

        return vm

    async def start_vm(self, vm_id: uuid.UUID, user: User):
        vm = await self.get_vm(vm_id, user)
        if self.proxmox.enabled:
             # self.proxmox.start_vm(vm.node.hostname, vm.proxmox_vmid)
             pass
        vm.status = VMStatus.ACTIVE
        await self.vm_repo.db.commit()

    async def stop_vm(self, vm_id: uuid.UUID, user: User):
        vm = await self.get_vm(vm_id, user)
        if self.proxmox.enabled:
             # self.proxmox.stop_vm(vm.node.hostname, vm.proxmox_vmid)
             pass
        vm.status = VMStatus.STOPPED
        await self.vm_repo.db.commit()

    async def delete_vm(self, vm_id: uuid.UUID, user: User):
        vm = await self.get_vm(vm_id, user)
        if self.proxmox.enabled:
             # self.proxmox.delete_vm(vm.node.hostname, vm.proxmox_vmid)
             pass
        await self.vm_repo.delete(vm)
        await self.vm_repo.db.commit()
