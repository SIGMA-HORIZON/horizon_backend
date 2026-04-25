"""
Helper script to map your Proxmox cluster resources to Horizon.
Usage: Edit the MAPPINGS dictionary below and run:
python setup_proxmox_mappings.py
"""

import sys
import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Path adjustment to import horizon modules
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from horizon.shared.models import ISOImage, IsoProxmoxTemplate, ProxmoxNodeMapping, PhysicalNode

# --------------------------------------------------------------------------
# CONFIGURATION : Edit these values to match your Proxmox setup
# --------------------------------------------------------------------------

# Map PhysicalNode (REM, RAM, EMILIA) to your Proxmox node name (e.g., "pve1")
NODE_MAPPINGS = {
    PhysicalNode.REM: "pve1",
    PhysicalNode.RAM: "pve1",      # You can map multiple to the same node
    PhysicalNode.EMILIA: "pve1",
}

# Map ISO filename to Proxmox Template VMID
# To see available ISOs, run the script once; it will list them if they exist.
ISO_TEMPLATE_MAPPINGS = {
    "ubuntu-22.04-live-server-amd64.iso": 9000,
    "debian-12.4.0-amd64-netinst.iso": 9001,
}
# --------------------------------------------------------------------------

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://horizon:horizon@localhost:5432/horizon")

def setup():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("--- Setting up Proxmox Node Mappings ---")
        for p_node, px_name in NODE_MAPPINGS.items():
            existing = session.query(ProxmoxNodeMapping).filter_by(physical_node=p_node).first()
            if existing:
                print(f"Updating {p_node} -> {px_name}")
                existing.proxmox_node_name = px_name
            else:
                print(f"Creating {p_node} -> {px_name}")
                mapping = ProxmoxNodeMapping(physical_node=p_node, proxmox_node_name=px_name)
                session.add(mapping)

        print("\n--- Setting up ISO Template Mappings ---")
        isos = session.query(ISOImage).all()
        if not isos:
            print("No ISO images found in database. Please run seed.py first.")
            return

        for iso in isos:
            vmid = ISO_TEMPLATE_MAPPINGS.get(iso.filename)
            if vmid:
                existing = session.query(IsoProxmoxTemplate).filter_by(iso_image_id=iso.id).first()
                if existing:
                    print(f"Updating ISO {iso.filename} -> VMID {vmid}")
                    existing.proxmox_template_vmid = vmid
                else:
                    print(f"Mapping ISO {iso.filename} -> VMID {vmid}")
                    tpl = IsoProxmoxTemplate(iso_image_id=iso.id, proxmox_template_vmid=vmid)
                    session.add(tpl)
            else:
                print(f"Skipping ISO {iso.filename} (No VMID mapping provided in script)")

        session.commit()
        print("\nSuccess! Your database is now mapped to your Proxmox resources.")

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    setup()
