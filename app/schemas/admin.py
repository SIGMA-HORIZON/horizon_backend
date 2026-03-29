from typing import List, Optional
import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, AliasPath
from app.models.enums import RoleType, AccountRequestStatus

class AccountRequestResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    organisation: Optional[str] = None
    justification: Optional[str] = None
    status: AccountRequestStatus
    submitted_at: datetime

    class Config:
        from_attributes = True

class ApproveRequest(BaseModel):
    role: RoleType = RoleType.USER
    group: Optional[str] = None

class ApproveResponse(BaseModel):
    user_id: uuid.UUID
    username: str
    email_sent: bool

class RejectRequest(BaseModel):
    reason: Optional[str] = None

class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=128)
    last_name: str = Field(..., min_length=2, max_length=128)
    email: EmailStr
    role: RoleType = RoleType.USER
    group: Optional[str] = None

class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    role: RoleType
    is_active: bool
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[RoleType] = None
    group: Optional[str] = None

class DeactivateRequest(BaseModel):
    reason: Optional[str] = None

class DeactivateResponse(BaseModel):
    message: str
    suspended_at: datetime
