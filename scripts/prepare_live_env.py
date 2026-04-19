import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Ensure the project root is in sys.path
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://horizon:horizon@localhost:5432/horizon"
)

def prepare_live_env():
    engine = create_engine(DATABASE_URL)
    
    tables_to_truncate = [
        "audit_logs",
        "login_attempts",
        "security_incidents",
        "quota_violations",
        "reservations",
        "virtual_machines",
        "iso_proxmox_templates",
        "proxmox_node_mappings",
        "iso_images",
        "quota_overrides",
        "account_requests"
    ]
    
    with engine.connect() as conn:
        print("Starting cleanup for live Proxmox integration...")
        
        for table in tables_to_truncate:
            print(f"  Truncating table: {table}")
            try:
                conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            except Exception as e:
                print(f"    Error truncating {table}: {e}")
        
        conn.commit()
        print("\nCleanup completed successfully.")
        print("Preserved tables: users, roles, role_permissions, quota_policies.")

if __name__ == "__main__":
    prepare_live_env()
