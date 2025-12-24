from app.models.base.character import CharacterBase


class CharacterCreate(CharacterBase):
    """Request body for creating a character."""
    pass


class CharacterRead(CharacterBase):
    """Response model for a character."""
    id: int
