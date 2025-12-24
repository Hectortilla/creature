from app.models.base.element import ElementBase


class ElementCreate(ElementBase):
    """Request body for creating an element."""
    pass


class ElementRead(ElementBase):
    """Response model for an element."""
    id: int
