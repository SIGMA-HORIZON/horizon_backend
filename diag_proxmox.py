
import sys
import os
sys.path.append(os.getcwd())

from horizon.infrastructure.proxmox_client import ProxmoxClient

def check_nodes():
    try:
        client = ProxmoxClient()
        if not client.enabled:
            print("Proxmox client is not enabled.")
            return

        nodes = client._api.nodes.get()
        print(f"\n{'Node':<15} | {'Status':<10} | {'CPU':<5} | {'Memory (GB)':<10}")
        print("-" * 50)
        for n in nodes:
            print(f"{n.get('node'):<15} | {n.get('status'):<10} | {n.get('cpu', 0):<5.2f} | {n.get('maxmem', 0)/1024/1024/1024:<10.2f}")

        # List all VMs on each node
        for n in nodes:
            node_name = n.get('node')
            print(f"\nVMs on node {node_name}:")
            vms = client._api.nodes(node_name).qemu.get()
            if not vms:
                print("  No VMs found.")
            for v in vms:
                print(f"  - {v.get('vmid')}: {v.get('name')} ({v.get('status')}) {'(Template)' if v.get('template') else ''}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_nodes()
