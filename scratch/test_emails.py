import sys
import os
from datetime import datetime

# Ajouter le chemin du projet au PYTHONPATH
sys.path.append(os.getcwd())

# Configurer les mocks pour éviter les erreurs de config manquantes si besoin
os.environ["EMAIL_MODE"] = "mock"
os.environ["APP_ENV"] = "development"

from horizon.infrastructure.email_service import (
    send_account_credentials,
    send_vm_created_notification,
    send_vm_stopped_notification,
    send_vm_deleted_notification,
)

print("--- TEST DES EMAILS (MODE MOCK) ---")

print("\n1. Test Credentials:")
send_account_credentials("test@example.com", "jdoe", "Secret123!")

print("\n2. Test VM Created:")
send_vm_created_notification("test@example.com", "My-Project-VM", "192.168.1.50", "27/04/2026 20:00")

print("\n3. Test VM Stopped:")
send_vm_stopped_notification("test@example.com", "My-Project-VM")

print("\n4. Test VM Deleted:")
send_vm_deleted_notification("test@example.com", "My-Project-VM")

print("\n--- FIN DU TEST ---")
