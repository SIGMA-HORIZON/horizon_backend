import requests
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "alice.mvondo"
PASSWORD = "Student@2025!"

def main():
    print(f"--- Automated Live Test: {BASE_URL} ---")
    
    # 1. Login
    print("\n1. Logging in...")
    login_url = f"{BASE_URL}/auth/login"
    payload = {"username": USERNAME, "password": PASSWORD}
    try:
        resp = requests.post(login_url, json=payload)
        if resp.status_code == 404:
            print(f"404 at {login_url}. Trying alternative...")
            login_url = "http://localhost:8000/auth/login"
            resp = requests.post(login_url, json=payload)
        
        resp.raise_for_status()
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"Success: Logged in via {login_url}.")
    except Exception as e:
        print(f"Error logging in: {e}")
        return

    # 2. Get ISO list
    print("\n2. Fetching available ISOs...")
    try:
        resp = requests.get(f"{BASE_URL}/vms/isos", headers=headers)
        resp.raise_for_status()
        isos = resp.json()["items"]
        if not isos:
            print("No ISOs found. Seed the database first.")
            return
        
        # Prefer Ubuntu 22.04 if available, otherwise take the first
        iso = next((i for i in isos if "ubuntu-22.04" in i["name"]), isos[0])
        iso_id = iso["id"]
        print(f"Using ISO: {iso['name']} ({iso_id})")
    except Exception as e:
        print(f"Error fetching ISOs: {e}")
        return

    # 3. Create VM
    print("\n3. Creating VM on Proxmox...")
    vm_name = f"test-live-{int(time.time())}"
    payload = {
        "name": vm_name,
        "iso_image_id": iso_id,
        "vcpu": 1,
        "ram_gb": 1,
        "storage_gb": 10,
        "session_hours": 1,
        "description": "Live cluster test from agent"
    }
    try:
        resp = requests.post(f"{BASE_URL}/vms", headers=headers, json=payload)
        resp.raise_for_status()
        vm = resp.json()
        vm_id = vm["id"]
        vmid = vm["proxmox_vmid"]
        print(f"Success: VM '{vm_name}' created. ID: {vm_id}, VMID: {vmid}")
    except Exception as e:
        print(f"Error creating VM: {e}")
        if 'resp' in locals() and resp.status_code == 422:
            print(f"Detail: {resp.json()}")
        return

    print("\nVM is being cloned and started on Proxmox. Waiting 15s for it to initialize...")
    time.sleep(15)

    # 4. Stop VM
    print("\n4. Stopping VM...")
    try:
        resp = requests.post(f"{BASE_URL}/vms/{vm_id}/stop", headers=headers)
        resp.raise_for_status()
        print("Success: Stop command sent.")
    except Exception as e:
        print(f"Error stopping VM: {e}")

    print("Waiting 10s...")
    time.sleep(10)

    # 5. Start VM
    print("\n5. Starting VM...")
    try:
        resp = requests.post(f"{BASE_URL}/vms/{vm_id}/start", headers=headers)
        resp.raise_for_status()
        print("Success: Start command sent.")
    except Exception as e:
        print(f"Error starting VM: {e}")

    print("Waiting 10s...")
    time.sleep(10)

    # 6. Delete VM
    print("\n6. Deleting VM (Purge from Proxmox)...")
    try:
        resp = requests.delete(f"{BASE_URL}/vms/{vm_id}", headers=headers)
        resp.raise_for_status()
        print("Success: Deletion command sent.")
    except Exception as e:
        print(f"Error deleting VM: {e}")

    print("\n--- Live Test Completed ---")

if __name__ == "__main__":
    main()
