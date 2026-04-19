
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from horizon.shared.models import VirtualMachine
from horizon.core.config import get_settings

def check_db_vms():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    vms = db.query(VirtualMachine).all()
    print(f"VMs in DB: {len(vms)}")
    for vm in vms:
        print(f"ID: {vm.id}, Proxmox VMID: {vm.proxmox_vmid}, Name: {vm.name}, Status: {vm.status.value}")
    
    db.close()

if __name__ == "__main__":
    check_db_vms()
