from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.enums import ActionType

class AuditLogBase(BaseModel):
    action_type: ActionType
    description: Optional[str] = None
    ip_address: Optional[str] = None
    success: bool = True

class AuditLog(AuditLogBase):
    id: UUID
    user_id: Optional[UUID] = None
    occurred_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
