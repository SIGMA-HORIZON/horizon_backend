
from horizon.core.config import get_settings
import os

def check_env():
    settings = get_settings()
    print(f"Settings PROXMOX_TIMEOUT: {settings.PROXMOX_TIMEOUT}")
    print(f"OS ENV PROXMOX_TIMEOUT: {os.getenv('PROXMOX_TIMEOUT')}")

if __name__ == "__main__":
    check_env()
