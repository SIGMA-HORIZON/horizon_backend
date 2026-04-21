
import sys
import os
sys.path.append(os.getcwd())

from horizon.infrastructure.proxmox_client import ProxmoxClient

def list_isos():
    try:
        client = ProxmoxClient()
        if not client.enabled:
            return

        storage = client._api.nodes("pve").storage("local").content.get()
        print(f"\nFiles on 'local' storage:")
        for f in storage:
            if f.get('content') == 'iso':
                print(f"  - {f.get('volid')} ({f.get('size')/1024/1024:.2f} MB)")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_isos()
