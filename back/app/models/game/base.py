"""
Game Base Model

Provides the base class for all game models.
"""

from pydantic import BaseModel, ConfigDict


class GameBaseModel(BaseModel):
    """
    Base class for all game models.
    
    Provides consistent configuration and serialization behavior.
    Uses Pydantic v2 with:
    - model_dump() for dict serialization
    - model_dump_json() for JSON string
    - model_validate() for creating from dict
    """
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        use_enum_values=False,
    )


__all__ = ["GameBaseModel"]

