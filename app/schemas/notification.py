from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from app.models.enums import NotifType

class NotificationBase(BaseModel):
    notif_type: NotifType
    message: str
    is_read: bool = False

class Notification(NotificationBase):
    id: UUID
    user_id: UUID
    sent_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
