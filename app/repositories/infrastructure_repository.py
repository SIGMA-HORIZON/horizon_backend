from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base_models import PhysicalNode, ISOImage

class InfrastructureRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_nodes(self) -> List[PhysicalNode]:
        query = select(PhysicalNode).where(PhysicalNode.status == "online")
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_iso(self, id: uuid.UUID) -> Optional[ISOImage]:
        query = select(ISOImage).where(ISOImage.id == id).where(ISOImage.is_active == True)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_isos(self) -> List[ISOImage]:
        query = select(ISOImage).where(ISOImage.is_active == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())
