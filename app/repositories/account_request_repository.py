from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base_models import AccountRequest
from app.models.enums import AccountRequestStatus

class AccountRequestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, request_id: uuid.UUID) -> Optional[AccountRequest]:
        query = select(AccountRequest).where(AccountRequest.id == request_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_requests(self, status: Optional[AccountRequestStatus] = None) -> List[AccountRequest]:
        query = select(AccountRequest)
        if status:
            query = query.where(AccountRequest.status == status)
        query = query.order_by(AccountRequest.submitted_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, request: AccountRequest) -> AccountRequest:
        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)
        return request
