from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.enums import VMStatus

class VMBase(BaseModel):
    name: str = Field(..., max_length=128)
    cpu_cores: int = Field(..., gt=0)
    ram_gb: int = Field(..., gt=0)
    disk_gb: int = Field(..., gt=0)
    duration_hours: int = Field(..., gt=0)

class VMCreate(VMBase):
    policy_id: UUID
    node_id: UUID
    iso_image_id: UUID
    ssh_key_id: UUID

class VMUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    status: Optional[VMStatus] = None

class VM(VMBase):
    id: UUID
    user_id: UUID
    policy_id: UUID
    node_id: UUID
    iso_image_id: UUID
    ssh_key_id: UUID
    status: VMStatus
    start_time: datetime
    end_time: datetime
    created_at: datetime
    last_activity_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
