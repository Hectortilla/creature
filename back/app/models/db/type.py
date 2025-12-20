from sqlmodel import SQLModel, Field


class Type(SQLModel, table=True):
    __tablename__ = "types"
    
    id: int | None = Field(default=None, primary_key=True)
    label: str = Field(max_length=100, unique=True)
    icon: str | None = Field(default=None, max_length=255)

