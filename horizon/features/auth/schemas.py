"""Schémas Pydantic — auth."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_change_pwd: bool = False
    role: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Minimum 10 caractères requis.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Au moins une majuscule requise.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Au moins une minuscule requise.")
        if not re.search(r"\d", v):
            raise ValueError("Au moins un chiffre requis.")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;':\",./<>?]", v):
            raise ValueError("Au moins un caractère spécial requis.")
        return v

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Les mots de passe ne correspondent pas.")
        return self


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    organisation: str | None
    role: str
    is_active: bool
    must_change_pwd: bool
    last_login_at: datetime | None = None
    created_at: datetime

    @field_validator("role", mode="before")
    @classmethod
    def role_to_str(cls, v):
        return v.value if hasattr(v, "value") else v
