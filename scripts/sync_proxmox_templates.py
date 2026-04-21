
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from horizon.shared.models import IsoProxmoxTemplate, ISOImage
from horizon.infrastructure.proxmox_client import ProxmoxClient
from horizon.core.config import get_settings

def sync_templates():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        client = ProxmoxClient()
        if not client.enabled:
            print("Proxmox is not enabled or configured.")
            return

        # Get all nodes
        nodes = client.api.nodes.get()
        
        # Get all ISOs from DB
        db_isos = db.query(ISOImage).all()
        iso_map = {iso.name.lower(): iso for iso in db_isos}
        iso_file_map = {iso.filename.lower(): iso for iso in db_isos}
        
        for node in nodes:
            node_name = node['node']
            vms = client.api.nodes(node_name).qemu.get()
            
            for vm in vms:
                is_template = vm.get('template') == 1
                vmid = vm.get('vmid')
                vm_name = vm.get('name', '').lower()
                
                if is_template:
                    print(f"Found template: {vm_name} (VMID: {vmid}) on node {node_name}")
                    
                    # Check if already mapped
                    existing = db.query(IsoProxmoxTemplate).filter(IsoProxmoxTemplate.proxmox_template_vmid == vmid).first()
                    if existing:
                        print(f"  Already mapped to ISO ID: {existing.iso_image_id}")
                        continue
                    
                    # Heuristic to match with ISO
                    matched_iso = None
                    # Try direct match
                    for iso_name, iso_obj in iso_map.items():
                        if iso_name in vm_name or vm_name in iso_name:
                            matched_iso = iso_obj
                            break
                    
                    if not matched_iso:
                        # Try fuzzy match on prefix (especially for alpine-virt)
                        for iso_name, iso_obj in iso_map.items():
                            prefix = iso_name.split('-')[0:2] # e.g. ['alpine', 'virt']
                            prefix_str = "-".join(prefix)
                            if prefix_str in vm_name:
                                matched_iso = iso_obj
                                break

                    if not matched_iso:
                        # Try filename matching (prefix)
                        for iso_filename, iso_obj in iso_file_map.items():
                            fname_prefix = iso_filename.split('-')[0:2]
                            fname_prefix_str = "-".join(fname_prefix)
                            if fname_prefix_str in vm_name:
                                matched_iso = iso_obj
                                break
                    
                    if matched_iso:
                        print(f"  Matched with ISO: {matched_iso.name}. Creating mapping...")
                        new_mapping = IsoProxmoxTemplate(
                            iso_image_id=matched_iso.id,
                            proxmox_template_vmid=vmid
                        )
                        db.add(new_mapping)
                        db.commit()
                        print(f"  Success: Mapped {vm_name} to {matched_iso.name}")
                    else:
                        print(f"  Could not match template '{vm_name}' with any ISO in database.")

    except Exception as e:
        print(f"Error during synchronization: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Add project root to path so horizon package can be found
    # Assuming script is in scripts/ or root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) if "scripts" in script_dir else script_dir
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    sync_templates()
