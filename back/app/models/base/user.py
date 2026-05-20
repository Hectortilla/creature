from sqlmodel import SQLModel


class UserBase(SQLModel):
    """Base user model with common fields."""
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool = False
    
    def __str__(self) -> str:
        return self.username

