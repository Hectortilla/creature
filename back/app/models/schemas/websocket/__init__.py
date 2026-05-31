"""
WebSocket Message Schemas

These schemas define the structure of all WebSocket messages.
They're exposed via dummy HTTP endpoints to generate TypeScript types.
"""

from typing import Any

from pydantic import BaseModel

# ============================================================================
# Base Message Class
# ============================================================================


class WebSocketMessage(BaseModel):
    """Base class for WebSocket messages that ensures type is included in serialization."""

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Override to include the ClassVar type in serialization."""
        result = super().model_dump(**kwargs)
        # Include the type from the class variable
        result["type"] = self.__class__.type
        return result
