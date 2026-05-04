
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from horizon.shared.models.proxmox_mapping import ProxmoxNodeMapping
from horizon.core.config import get_settings

def update_mappings():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    mappings = db.query(ProxmoxNodeMapping).all()
    print(f"Updating {len(mappings)} mappings to use 'pve' node name...")
    for m in mappings:
        print(f"Changing {m.physical_node.value}: {m.proxmox_node_name} -> pve")
        m.proxmox_node_name = "pve"
    
    db.commit()
    db.close()
    print("Update complete.")

if __name__ == "__main__":
    update_mappings()
