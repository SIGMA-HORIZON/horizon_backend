
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from horizon.shared.models.proxmox_mapping import ProxmoxNodeMapping
from horizon.core.config import get_settings

def check_mappings():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    mappings = db.query(ProxmoxNodeMapping).all()
    print(f"Total mappings: {len(mappings)}")
    for m in mappings:
        print(f"Physical: {m.physical_node.value}, Proxmox Node: {m.proxmox_node_name}")
    
    db.close()

if __name__ == "__main__":
    check_mappings()
