
import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from horizon.core.config import get_settings
from horizon.shared.models import IsoProxmoxTemplate, ISOImage

def list_templates():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        templates = db.query(IsoProxmoxTemplate).all()
        print(f"\n{'ISO Image ID':<38} | {'ISO Name':<30} | {'Proxmox Template VMID':<20}")
        print("-" * 100)
        for t in templates:
            iso = db.query(ISOImage).filter(ISOImage.id == t.iso_image_id).first()
            name = iso.name if iso else "Unknown"
            print(f"{str(t.iso_image_id):<38} | {name:<30} | {t.proxmox_template_vmid:<20}")
    finally:
        db.close()

if __name__ == "__main__":
    list_templates()
