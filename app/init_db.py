import asyncio
import sys
import os

# Ajouter le répertoire parent au sys.path pour permettre les imports de 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import Base, engine
# Importation de tous les modèles pour qu'ils soient enregistrés dans Base.metadata
from app.models.base_models import Role, User, AuditLog, UsagePolicy, Quota, PhysicalNode, ISOImage, SSHKey, VirtualMachine, Notification

async def init_db():
    print(f"Connexion à la base de données pour l'initialisation...")
    try:
        async with engine.begin() as conn:
            # Création des tables
            print("Création des tables et des types ENUM...")
            await conn.run_sync(Base.metadata.create_all)
            print("Base de données initialisée avec succès !")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base : {e}")

if __name__ == "__main__":
    asyncio.run(init_db())
