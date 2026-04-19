
from proxmoxer import ProxmoxAPI
from horizon.core.config import get_settings
import urllib3

def punch_vm(vmid):
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
    
    node = "pve"
    try:
        print(f"Deleting VM {vmid} on node {node}...")
        api.nodes(node).qemu(vmid).delete(purge=1)
        print("Success.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    punch_vm(116)
