from sqlmodel import SQLModel, Field


class AttackBase(SQLModel):
    code: int
    name: str = Field(max_length=255)
    description: str | None = None
    damage: int | None = None
    type: str | None = Field(default=None, max_length=50)
    dice_rolls: int | None = None
    necessary_force: list[dict] | None = None
    effect: str | None = None

