import sys
import os

# Ajouter le chemin du projet au PYTHONPATH
sys.path.append(os.getcwd())

from horizon.core.config import get_settings

def test_config():
    settings = get_settings()
    print("--- Proxmox Configuration Check ---")
    print(f"PROXMOX_ENABLED: {settings.PROXMOX_ENABLED}")
    print(f"PROXMOX_HOST: {settings.PROXMOX_HOST}")
    print(f"PROXMOX_PORT: {settings.PROXMOX_PORT}")
    print(f"PROXMOX_USER: {settings.PROXMOX_USER}")
    print(f"PROXMOX_TOKEN_NAME: {settings.PROXMOX_TOKEN_NAME}")
    print(f"PROXMOX_TOKEN_VALUE: {'****' if settings.PROXMOX_TOKEN_VALUE else 'Empty'}")
    print(f"PROXMOX_VERIFY_SSL: {settings.PROXMOX_VERIFY_SSL}")
    print(f"PROXMOX_NODE: {settings.PROXMOX_NODE}")
    print("-----------------------------------")

if __name__ == "__main__":
    test_config()
