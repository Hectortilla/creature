from sqlmodel import SQLModel, Field
from app.utils.enums import ActionType

from app.models.core.attack import AttackCoreFields


class AttackBase(AttackCoreFields, SQLModel):
    """
    Base attack model for database.
    
    Inherits shared fields from:
    - AttackCoreFields: name, description, damage, effect, dice_rolls
    
    Adds DB-specific fields: code, type (as string), necessary_force (as dict)
    """
    code: int
    # Override with Field constraints for DB
    name: str = Field(max_length=255)
    type: ActionType | None = Field(default=ActionType.physical, max_length=50)
    necessary_force: list[dict] | None = None
    dice_rolls: list[dict] | None = None
    
    def __str__(self) -> str:
        return self.name

