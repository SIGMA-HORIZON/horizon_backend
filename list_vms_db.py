
import sys
import os

# Ajouter le dossier parent au path pour importer horizon
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from horizon.core.config import get_settings
from horizon.shared.models import VirtualMachine, User

def list_vms():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        vms = db.query(VirtualMachine).all()
        print(f"\n{'ID (UUID)':<38} | {'VMID':<6} | {'Nom':<20} | {'Status':<10} | {'Utilisateur':<15} | {'Node':<10}")
        print("-" * 115)
        
        for vm in vms:
            owner = db.query(User).filter(User.id == vm.owner_id).first()
            username = owner.username if owner else "Inconnu"
            print(f"{str(vm.id):<38} | {vm.proxmox_vmid:<6} | {vm.name:<20} | {vm.status.value:<10} | {username:<15} | {vm.node.value:<10}")
            
    finally:
        db.close()

if __name__ == "__main__":
    list_vms()
