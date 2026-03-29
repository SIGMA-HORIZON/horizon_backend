from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base_models import User, Role
from app.models.enums import RoleType

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(User).options(joinedload(User.role)).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        query = select(User).options(joinedload(User.role)).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_active_admins(self) -> List[User]:
        query = (
            select(User)
            .join(Role)
            .where(Role.role_type == RoleType.ADMIN)
            .where(User.is_active == True)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, user_in: User) -> User:
        self.db.add(user_in)
        await self.db.commit()
        await self.db.refresh(user_in)
        return user_in

    async def update(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
