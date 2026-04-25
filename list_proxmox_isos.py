
import sys
import os
import json
from dotenv import load_dotenv

sys.path.append(os.getcwd())

from horizon.core.config import get_settings
from horizon.infrastructure.proxmox_client import ProxmoxClient

def list_isos():
    load_dotenv()
    client = ProxmoxClient()
    nodes = client._api.nodes.get()
    
    for node in nodes:
        node_name = node['node']
        print(f"\nNode: {node_name}")
        
        storages = client._api.nodes(node_name).storage.get()
        for storage in storages:
            # print(f"DEBUG: {storage}")
            storage_name = storage['storage']
            # On vérifie si le stockage peut contenir des ISO
            content_types = storage.get('content', '').split(',')
            if 'iso' in content_types:
                print(f"  Storage: {storage_name}")
                try:
                    content = client._api.nodes(node_name).storage(storage_name).content.get()
                    isos = [item for item in content if item['content'] == 'iso']
                    if not isos:
                        print("    (Aucun ISO trouvé)")
                    for iso in isos:
                        print(f"    - {iso['volid']} ({iso.get('size', 0)/(1024*1024*1024):.2f} GB)")
                except Exception as e:
                    print(f"    (Erreur access storage: {e})")

if __name__ == "__main__":
    list_isos()
