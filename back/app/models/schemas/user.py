from pydantic import BaseModel
from datetime import datetime

from app.models.base.user import UserBase


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    username: str
    email: str | None = None
    full_name: str | None = None
    password: str


class UserRead(UserBase):
    """Schema for reading user data (excludes password)."""
    id: int
    created_at: datetime


class Token(BaseModel):
    """Schema for access token response."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for token payload data."""
    username: str | None = None

