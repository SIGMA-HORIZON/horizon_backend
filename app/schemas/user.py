from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=128)
    last_name: str = Field(..., min_length=1, max_length=128)
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role_id: UUID

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=128)
    last_name: Optional[str] = Field(None, max_length=128)
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None

class User(UserBase):
    id: UUID
    role_id: UUID
    created_at: datetime
    last_login: Optional[datetime] = None
    suspended_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
