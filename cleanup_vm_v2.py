
from proxmoxer import ProxmoxAPI
from horizon.core.config import get_settings
import urllib3
import time

def cleanup_vmid(vmid):
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
        # Check if exists
        vms = api.nodes(node).qemu.get()
        exists = any(v['vmid'] == vmid for v in vms)
        if not exists:
            print(f"VM {vmid} does not exist. Checking for config file residuals...")
            # Sometimes config exists but not in qemu list? Unlikely but...
        
        print(f"Stopping VM {vmid} just in case...")
        try:
            api.nodes(node).qemu(vmid).status.stop.post()
            time.sleep(2)
        except:
            pass
            
        print(f"Deleting VM {vmid} (purge=1)...")
        api.nodes(node).qemu(vmid).delete(purge=1)
        
        # Wait a bit
        for _ in range(5):
            time.sleep(1)
            vms = api.nodes(node).qemu.get()
            if not any(v['vmid'] == vmid for v in vms):
                print(f"VM {vmid} successfully deleted.")
                return
        print(f"VM {vmid} still exists after 5 seconds.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    cleanup_vmid(116)
