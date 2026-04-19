# Testing VM Creation on Proxmox

Follow these steps to verify that the backend correctly creates VMs on your local Proxmox cluster.

## 1. Configure the Environment
Ensure your `.env` file contains the correct Proxmox credentials and that the feature is enabled:

```env
PROXMOX_ENABLED=True
PROXMOX_HOST=your-proxmox-ip
PROXMOX_USER=your-user@pve
PROXMOX_TOKEN_NAME=your-token-id
PROXMOX_TOKEN_VALUE=your-token-secret
PROXMOX_VERIFY_SSL=False
```

## 2. Set Up Database Mappings
The database needs to know which Physical Node corresponds to which Proxmox Node, and which ISO corresponds to which Proxmox Template.

1.  **Seed the database** (if not already done):
    ```bash
    python scripts/seed.py
    ```
2.  **Configure mappings**:
    Edit the `setup_proxmox_mappings.py` script I created in the root directory to match your Proxmox node names and template VMIDs, then run it:
    ```bash
    python setup_proxmox_mappings.py
    ```

## 3. Start the Backend
```bash
uvicorn horizon.main:app --reload
```

## 4. Create a VM via API
Open the Swagger UI at `http://localhost:8000/docs` or use `curl` to create a VM.

### Find a valid ISO UUID first:
Run this command in your terminal to list all available ISOs and find their IDs:
```bash
curl -X GET http://localhost:8000/api/v1/vms/isos -H "Authorization: Bearer YOUR_TOKEN"
```
*(Or check the `iso_images` table directly in your database)*

### Create the VM:
Use the ID you found in the request body below:

**Sample Request Body:**
```json
{
  "name": "test-proxmox-vm",
  "iso_image_id": "PASTE_REAL_UUID_HERE",
  "vcpu": 1,
  "ram_gb": 1,
  "storage_gb": 10,
  "session_hours": 2,
  "description": "Verification of Proxmox cluster interaction"
}
```

## 5. Verify on Proxmox
Check your Proxmox web interface. You should see a new task for cloning the template and starting the new VM!
