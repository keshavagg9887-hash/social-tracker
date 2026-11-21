"""Authentication Data Transfer Objects & Schemas [M3]."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    """JWT Token response returned upon login/registration."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    role: str


class LoginRequest(BaseModel):
    """Credentials payload for login."""
    email: EmailStr
    password: str = Field(..., min_length=4)


class RegisterRequest(BaseModel):
    """Payload for user account creation."""
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    role: Optional[str] = Field("handler", description="User role: admin, handler, viewer, authority")


class UserProfileResponse(BaseModel):
    """User profile response."""
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
