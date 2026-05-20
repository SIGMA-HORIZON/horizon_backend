"""
Horizon - Proxmox ISO Sync Script
Synchronise les ISOs physiques Proxmox avec la base de données.
Usage: python scripts/sync_isos.py
"""

import os
import sys
import uuid
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Ajout du chemin racine pour les imports horizon
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

load_dotenv()

from horizon.features.admin import service as admin_service
from horizon.shared.models import User

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://horizon_user:horizon_pass@localhost:5432/horizon_db"
)

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

async def run_sync():
    print(f"Connecting to database at {DATABASE_URL.split('@')[-1]}...")
    db = Session()
    try:
        # Trouver un administrateur pour l'audit
        admin = db.query(User).filter(User.username == "admin.tamegue").first()
        if not admin:
            # Fallback sur n'importe quel admin
            admin = db.query(User).filter(User.role == "super_admin").first()
        
        if not admin:
            print("Erreur : Aucun administrateur trouvé en base pour effectuer la synchronisation.")
            return

        print(f"Starting ISO synchronization (as {admin.username})...")
        result = await admin_service.sync_isos_from_proxmox(db, admin.id)
        
        print(f"Success: {result['message']}")
        print(f"Added: {result['added']}, Updated: {result['updated']}")
        
    except Exception as e:
        print(f"Synchronization failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_sync())
