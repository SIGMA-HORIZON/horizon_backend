from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import Optional
from app.models.enums import RoleType

class RoleBase(BaseModel):
    role_type: RoleType
    description: Optional[str] = Field(None, max_length=255)

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=255)

class Role(RoleBase):
    id: UUID
    
    model_config = ConfigDict(from_attributes=True)
