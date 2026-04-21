
import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from horizon.core.config import get_settings
from horizon.shared.models import ProxmoxNodeMapping

def list_mappings():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        mappings = db.query(ProxmoxNodeMapping).all()
        print(f"\n{'ID':<38} | {'Physical Node':<15} | {'Proxmox Node Name':<20}")
        print("-" * 75)
        for m in mappings:
            print(f"{str(m.id):<38} | {m.physical_node.value:<15} | {m.proxmox_node_name:<20}")
    finally:
        db.close()

if __name__ == "__main__":
    list_mappings()
