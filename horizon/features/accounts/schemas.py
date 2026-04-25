"""Schémas Pydantic - comptes."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator

from horizon.features.auth.schemas import UserResponse


class AccountRequestCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    organisation: str
    justification: str | None = None


class AccountRequestResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    first_name: str
    last_name: str
    email: str
    organisation: str
    status: str
    created_at: datetime

    @field_validator("status", mode="before")
    @classmethod
    def status_to_str(cls, v):
        return v.value if hasattr(v, "value") else v


class AccountRequestListResponse(BaseModel):
    items: list[AccountRequestResponse]


class AdminCreateUser(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    organisation: str | None = None
    role: str = "USER"
    quota_policy_id: str | None = None


class AdminUpdateUser(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    organisation: str | None = None
    role: str | None = None
    quota_policy_id: str | None = None


class ApproveRequestBody(BaseModel):
    quota_policy_id: str | None = None


class ApproveAccountResponse(BaseModel):
    message: str
    username: str


class RejectRequestBody(BaseModel):
    reason: str


class UserListResponse(BaseModel):
    items: list[UserResponse]
