
from proxmoxer import ProxmoxAPI
from horizon.core.config import get_settings
import urllib3

def list_actual_nodes():
    settings = get_settings()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    api = ProxmoxAPI(
        settings.PROXMOX_HOST,
        user=settings.PROXMOX_USER,
        token_name=settings.PROXMOX_TOKEN_ID,
        token_value=settings.PROXMOX_TOKEN_SECRET,
        verify_ssl=settings.PROXMOX_VERIFY_SSL,
        timeout=10
    )
    
    nodes = api.nodes.get()
    print("Actual Proxmox Nodes:")
    for node in nodes:
        print(f"Node Name: {node['node']}, Status: {node['status']}, CPU: {node.get('cpu')}")

if __name__ == "__main__":
    list_actual_nodes()
