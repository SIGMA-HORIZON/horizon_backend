from horizon.shared.models import VirtualMachine, IsoProxmoxTemplate, Reservation, QuotaViolation, SecurityIncident, AuditLog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://horizon_user:horizon_pass@localhost:5432/horizon_db"
)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def cleanup():
    session = Session()
    try:
        print("Starting comprehensive cleanup of seeded data...")
        
        # 1. Purge all IsoProxmoxTemplate records
        templates_deleted = session.query(IsoProxmoxTemplate).delete()
        print(f"  Deleted {templates_deleted} template mappings.")
        
        # 2. Purge all ISOImage records
        isos_deleted = session.query(ISOImage).delete()
        print(f"  Deleted {isos_deleted} ISO images.")
        
        # 3. VMs (VMID between 100 and 200 in our seed)
        vms_to_delete = session.query(VirtualMachine).filter(VirtualMachine.proxmox_vmid.between(100, 200)).all()
        vm_ids = [vm.id for vm in vms_to_delete]
        
        if vm_ids:
            session.query(Reservation).filter(Reservation.vm_id.in_(vm_ids)).delete(synchronize_session=False)
            session.query(QuotaViolation).filter(QuotaViolation.vm_id.in_(vid for vid in vm_ids)).delete(synchronize_session=False)
            session.query(SecurityIncident).filter(SecurityIncident.vm_id.in_(vid for vid in vm_ids)).delete(synchronize_session=False)
            str_vm_ids = [str(vid) for vid in vm_ids]
            session.query(AuditLog).filter(AuditLog.target_id.in_(str_vm_ids)).delete(synchronize_session=False)
            
            vms_deleted = session.query(VirtualMachine).filter(VirtualMachine.id.in_(vm_ids)).delete(synchronize_session=False)
            print(f"  Deleted {vms_deleted} placeholder virtual machines.")
        
        session.commit()
        print("Cleanup completed successfully.")
    except Exception as e:
        session.rollback()
        print(f"ERROR during cleanup: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    cleanup()
