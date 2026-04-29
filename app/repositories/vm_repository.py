from typing import List, Optional
import uuid
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base_models import VirtualMachine

class VMRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, id: uuid.UUID) -> Optional[VirtualMachine]:
        query = select(VirtualMachine).where(VirtualMachine.id == id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_by_user(self, user_id: uuid.UUID) -> List[VirtualMachine]:
        query = select(VirtualMachine).where(VirtualMachine.user_id == user_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[VirtualMachine]:
        query = select(VirtualMachine).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        query = select(func.count()).select_from(VirtualMachine)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def create(self, vm: VirtualMachine) -> VirtualMachine:
        self.db.add(vm)
        await self.db.flush() # Using flush to let the service handle the commit if needed
        return vm

    async def delete(self, vm: VirtualMachine) -> None:
        await self.db.delete(vm)
        await self.db.flush()
