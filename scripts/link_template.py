
import uuid
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Ajout du path pour trouver les modèles
sys.path.append(os.getcwd())

from horizon.shared.models import ISOImage, IsoProxmoxTemplate

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def link_template(iso_name_pattern, proxmox_vmid):
    session = Session()
    try:
        # 1. Trouver l'ISO
        iso = session.query(ISOImage).filter(ISOImage.name.ilike(f"%{iso_name_pattern}%")).first()
        if not iso:
            print(f"ISO '{iso_name_pattern}' non trouvée dans la base de données.")
            return

        # 2. Supprimer un ancien mapping s'il existe
        session.query(IsoProxmoxTemplate).filter(IsoProxmoxTemplate.iso_image_id == iso.id).delete()
        
        # 3. Créer le nouveau mapping
        new_mapping = IsoProxmoxTemplate(
            id=uuid.uuid4(),
            iso_image_id=iso.id,
            proxmox_template_vmid=proxmox_vmid
        )
        session.add(new_mapping)
        session.commit()
        print(f"SUCCESS: L'ISO '{iso.name}' est maintenant liée au VMID Proxmox {proxmox_vmid}.")
        
    except Exception as e:
        session.rollback()
        print(f"ERREUR : {e}")
    finally:
        session.close()

if __name__ == "__main__":
    # On lie l'ID 100 à Ubuntu par défaut pour le test
    link_template("Ubuntu 22.04", 100)
