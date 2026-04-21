
import sys
import os
sys.path.append(os.getcwd())

from horizon.infrastructure.proxmox_client import ProxmoxClient

def check_proxmox():
    try:
        client = ProxmoxClient()
        if not client.enabled:
            print("Proxmox client is not enabled.")
            return

        resources = client._api.cluster.resources.get(type="vm")
        print(f"\n{'VMID':<10} | {'Node':<10} | {'Name':<20} | {'Type':<10} | {'Status':<10}")
        print("-" * 65)
        for r in resources:
            print(f"{r.get('vmid'):<10} | {r.get('node'):<10} | {r.get('name'):<20} | {r.get('type'):<10} | {r.get('status'):<10}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_proxmox()
