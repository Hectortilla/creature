from app.models.base.type import TypeBase


class TypeCreate(TypeBase):
    """Request body for creating a type."""
    pass


class TypeRead(TypeBase):
    """Response model for a type."""
    id: int
