from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.enums import RoleType


class UserProfile(BaseModel):
    """Schema returned for the authenticated user's own profile."""
    id: UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    must_change_password: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    role: RoleType

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        # Flatten role relationship → role_type string for serialization
        if hasattr(obj, "role") and obj.role is not None:
            data = {
                "id": obj.id,
                "username": obj.username,
                "email": obj.email,
                "first_name": obj.first_name,
                "last_name": obj.last_name,
                "is_active": obj.is_active,
                "must_change_password": obj.must_change_password,
                "last_login": obj.last_login,
                "created_at": obj.created_at,
                "role": obj.role.role_type,
            }
            return cls(**data)
        return super().model_validate(obj, *args, **kwargs)


class UserProfileUpdate(BaseModel):
    """Allows a user to update only their own name fields."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=128)
    last_name: Optional[str] = Field(None, min_length=1, max_length=128)
