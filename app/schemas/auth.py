from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID

class RegisterRequest(BaseModel):
    last_name: str = Field(..., min_length=2, max_length=128)
    first_name: str = Field(..., min_length=2, max_length=128)
    email: EmailStr
    organisation: Optional[str] = Field(None, max_length=255)
    justification: Optional[str] = Field(None, max_length=1000)

class RegisterRequestResponse(BaseModel):
    message: str = "Your request has been submitted and is pending admin review."
    request_id: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    must_change_password: bool

class LogoutResponse(BaseModel):
    message: str = "Successfully logged out"

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
