from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from app.models.enums import OSType

class ISOImageBase(BaseModel):
    name: str = Field(..., max_length=128)
    os_type: OSType
    version: str = Field(..., max_length=64)
    proxmox_ref: str = Field(..., max_length=255)
    is_active: bool = True

class ISOImage(ISOImageBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
