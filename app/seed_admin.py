import asyncio
import sys
import os
from sqlalchemy import select

# Ajouter le répertoire parent au sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import AsyncSessionLocal
from app.models.base_models import User, Role
from app.models.enums import RoleType
from app.core.security import get_password_hash

async def seed_admin():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 1. Vérifier si les rôles existent, sinon les créer
            res = await session.execute(select(Role).where(Role.role_type == RoleType.ADMIN))
            admin_role = res.scalars().first()
            
            if not admin_role:
                print("Création des rôles de base...")
                admin_role = Role(role_type=RoleType.ADMIN, description="Administrator")
                user_role = Role(role_type=RoleType.USER, description="Standard User")
                session.add_all([admin_role, user_role])
                await session.flush() # Pour obtenir l'ID de l'admin_role

            # 2. Créer ou mettre à jour l'utilisateur administrateur
            res = await session.execute(
                select(User).where((User.email == "admin@horizon.api") | (User.username == "admin_principal"))
            )
            existing_admin = res.scalars().first()

            if not existing_admin:
                print("Création de l'administrateur par défaut...")
                new_admin = User(
                    username="admin_principal",
                    first_name="Admin",
                    last_name="Horizon",
                    email="admin@horizon.api",
                    password_hash=get_password_hash("admin123"),
                    role_id=admin_role.id,
                    is_active=True,
                    must_change_password=False
                )
                session.add(new_admin)
                print(f"Admin créé avec l'email: {new_admin.email}")
            else:
                print("Mise à jour de l'administrateur existant...")
                existing_admin.email = "admin@horizon.api"
                existing_admin.password_hash = get_password_hash("admin123")
                existing_admin.must_change_password = False
                existing_admin.is_active = True
                print(f"Admin mis à jour avec l'email: {existing_admin.email}")

if __name__ == "__main__":
    asyncio.run(seed_admin())
