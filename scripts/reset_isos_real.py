
import sys
import os
import uuid
from dotenv import load_dotenv

sys.path.append(os.getcwd())

from horizon.infrastructure.database import SessionLocal
from horizon.shared.models import ISOImage, IsoProxmoxTemplate, OSFamily

def reset_isos():
    load_dotenv()
    db = SessionLocal()
    try:
        # 1. Supprimer tout (les templates seront supprimés par cascade)
        print("Nettoyage des anciennes images ISO et templates...")
        db.query(IsoProxmoxTemplate).delete()
        db.query(ISOImage).delete()
        db.commit()

        # 2. Ajouter l'image réelle trouvée sur Proxmox
        real_iso = ISOImage(
            id=uuid.uuid4(),
            name="Ubuntu 22.04 Desktop (Proxmox)",
            filename="ubuntu-22.04.5-desktop-amd64.iso",
            os_family=OSFamily.LINUX,
            os_version="22.04.5",
            description="Image réelle détectée sur le serveur Proxmox.",
            is_active=True
        )
        db.add(real_iso)
        db.commit()
        db.refresh(real_iso)
        print(f"Ajouté : {real_iso.name} ({real_iso.filename})")

        # 3. Créer un template par défaut pour le VMID 100 (si c'est celui que vous voulez utiliser)
        tpl = IsoProxmoxTemplate(
            id=uuid.uuid4(),
            iso_image_id=real_iso.id,
            proxmox_template_vmid=100
        )
        db.add(tpl)
        db.commit()
        print(f"Template créé : {real_iso.name} -> VMID {tpl.proxmox_template_vmid}")

    except Exception as e:
        db.rollback()
        print(f"Erreur : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_isos()
