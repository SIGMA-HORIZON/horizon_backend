
from proxmoxer import ProxmoxAPI
from horizon.core.config import get_settings
import urllib3
import time

def cleanup_vmid_reliable(vmid):
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
        print(f"Checking for VM {vmid}...")
        vms = api.nodes(node).qemu.get()
        if not any(v['vmid'] == vmid for v in vms):
            print(f"VM {vmid} not found in qemu list.")
            return
            
        print(f"Found VM {vmid}. Attempting deletion...")
        upid = api.nodes(node).qemu(vmid).delete(purge=1)
        print(f"Deletion task started: {upid}")
        
        # Poll task status
        while True:
            status = api.nodes(node).tasks(upid).status.get()
            print(f"Task status: {status.get('status', 'RUNNING')}")
            if status.get('status') == 'stopped':
                exit_status = status.get('exitstatus')
                print(f"Task finished with exit status: {exit_status}")
                break
            time.sleep(2)
            
        # Final check
        vms = api.nodes(node).qemu.get()
        if not any(v['vmid'] == vmid for v in vms):
            print("VM successfully verified as deleted.")
        else:
            print("WARNING: VM still appears in list after task completion!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    cleanup_vmid_reliable(116)
