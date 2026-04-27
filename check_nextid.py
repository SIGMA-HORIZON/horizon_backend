
from proxmoxer import ProxmoxAPI
from horizon.core.config import get_settings
import urllib3

def check_nextid():
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
    
    try:
        nextid = api.cluster.nextid.get()
        print(f"Next available VMID on cluster: {nextid}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_nextid()
