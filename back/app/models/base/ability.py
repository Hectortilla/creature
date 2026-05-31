from sqlmodel import Field, SQLModel

from app.utils.enums import ActionType


class AbilityBase(SQLModel):
    code: int
    name: str = Field(max_length=255)
    description: str | None = None
    type: ActionType | None = Field(default=ActionType.physical, max_length=50)

    def __str__(self) -> str:
        return self.name
