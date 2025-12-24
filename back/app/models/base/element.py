from sqlmodel import SQLModel, Field


class ElementBase(SQLModel):
    label: str = Field(max_length=100)
    icon: str | None = Field(default=None, max_length=255)
    color: str | None = Field(default=None, max_length=50)
    strengths: list[int] | None = None
    weaknesses: list[int] | None = None

