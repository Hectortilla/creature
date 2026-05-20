from sqlmodel import SQLModel, Field


class AbilityBase(SQLModel):
    code: int
    name: str = Field(max_length=255)
    description: str | None = None
    type: str | None = Field(default=None, max_length=50)
    
    def __str__(self) -> str:
        return self.name

