
from proxmoxer import ProxmoxAPI
from horizon.core.config import get_settings
import urllib3

def check_vms():
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
    vms = api.nodes(node).qemu.get()
    print(f"VMs on node {node}:")
    for vm in vms:
        print(f"ID: {vm['vmid']}, Name: {vm['name']}, Status: {vm['status']}")

if __name__ == "__main__":
    check_vms()
