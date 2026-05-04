
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from horizon.shared.models import IsoProxmoxTemplate, ISOImage
from horizon.core.config import get_settings

def check_iso_templates():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    rows = db.query(IsoProxmoxTemplate).all()
    print(f"ISO Templates: {len(rows)}")
    for r in rows:
        iso = db.query(ISOImage).filter(ISOImage.id == r.iso_image_id).first()
        print(f"ISO: {iso.name if iso else '??'}, VMID: {r.proxmox_template_vmid}")
    
    db.close()

if __name__ == "__main__":
    check_iso_templates()
