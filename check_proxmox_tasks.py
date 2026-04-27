
from proxmoxer import ProxmoxAPI
from horizon.core.config import get_settings
import urllib3

def check_tasks():
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
    
    tasks = api.nodes("pve").tasks.get()
    print("Recent Tasks on pve:")
    for t in tasks[:10]:
        print(f"User: {t['user']}, Type: {t['type']}, Status: {t.get('status', 'RUNNING')}, ID: {t['id']}")

if __name__ == "__main__":
    check_tasks()
