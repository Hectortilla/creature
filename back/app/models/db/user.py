from sqlmodel import Field
from datetime import datetime

from app.models.base.user import UserBase


class User(UserBase, table=True):
    """User database model."""
    __tablename__ = "users"
    
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    email: str | None = Field(default=None, unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)

