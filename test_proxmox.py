
import sys
import os
from dotenv import load_dotenv

# Add the project root to sys.path
sys.path.append(os.getcwd())

from horizon.core.config import get_settings
from horizon.infrastructure.proxmox_client import ProxmoxClient, ProxmoxIntegrationError

def test_conn():
    load_dotenv()
    settings = get_settings()
    print(f"Testing Proxmox at {settings.PROXMOX_HOST}...")
    
    try:
        client = ProxmoxClient()
        if not client.enabled:
            print("ERROR: client not enabled")
            return
            
        print("Connected! Fetching version...")
        version = client._api.version.get()
        print(f"Proxmox Version: {version}")
        
        print("\nFetching nodes...")
        nodes = client._api.nodes.get()
        for node in nodes:
            node_name = node['node']
            print(f"- Node: {node_name} (Status: {node['status']}, CPU: {node.get('cpu', 0)*100:.1f}%)")
            
            # List VMs on this node
            vms = client._api.nodes(node_name).qemu.get()
            print(f"  VMS found ({len(vms)}):")
            for vm in vms:
                is_template = vm.get('template', 0) == 1
                type_str = "[TEMPLATE]" if is_template else "[VM]"
                print(f"    - {type_str} ID: {vm['vmid']} | Name: {vm['name']} | Status: {vm['status']}")
            
    except ProxmoxIntegrationError as e:
        print(f"Integration Error: {e.message}")
    except Exception as e:
        print(f"Unexpected Error: {e}")

if __name__ == "__main__":
    test_conn()
