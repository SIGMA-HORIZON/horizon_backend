import asyncio
import sys
import os
from sqlalchemy import text

# Ajouter le répertoire parent au sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import Base, engine
# Importation de tous les modèles pour qu'ils soient enregistrés dans Base.metadata
from app.models.base_models import Role, User, AuditLog, UsagePolicy, Quota, PhysicalNode, ISOImage, SSHKey, VirtualMachine, Notification

async def reset_db():
    print("WARNING: This will delete all data in the database!")
    
    async with engine.begin() as conn:
        # Drop all tables and dependencies by dropping the public schema
        print("Dropping schema public...")
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;")) # Ensure permissions are restored
        
        print("Creating all tables from current models...")
        await conn.run_sync(Base.metadata.create_all)
        
    print("Database reset successfully!")

if __name__ == "__main__":
    asyncio.run(reset_db())
