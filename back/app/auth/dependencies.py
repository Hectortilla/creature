"""
Authentication Dependencies

Provides FastAPI dependencies for user authentication via JWT tokens.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Query, WebSocket, WebSocketException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.auth.security import decode_access_token
from app.database import DBSessionDep, get_db_session
from app.models.db.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def _validate_token(token: str) -> str:
    """
    Validate JWT token and extract username.

    Returns:
        Username from token payload

    Raises:
        ValueError: If token is invalid or missing username
    """
    payload = decode_access_token(token)
    if payload is None:
        raise ValueError("Invalid token")

    username: str | None = payload.get("sub")
    if username is None:
        raise ValueError("Token missing username")

    return username


def _get_user_by_username(db: Session, username: str) -> User:
    """
    Look up a user by username directly. Kept in the auth layer (rather than
    delegating to a service) so that auth does not depend on app.services.

    Raises:
        ValueError: If user not found
    """
    user = db.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise ValueError("User not found")
    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
) -> User:
    """Dependency to get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        username = _validate_token(token)
        return _get_user_by_username(db, username)
    except ValueError:
        raise credentials_exception from None


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency to get the current active (non-disabled) user."""
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]


async def get_websocket_user(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
) -> User:
    """
    Dependency to authenticate WebSocket connections using JWT token.

    Token is passed as a query parameter since WebSocket handshakes
    don't support Authorization headers the same way as HTTP requests.

    Usage: ws://host/game/ws?token=<jwt_token>
    """
    credentials_exception = WebSocketException(
        code=status.WS_1008_POLICY_VIOLATION,
        reason="Could not validate credentials",
    )

    try:
        username = _validate_token(token)
    except ValueError:
        raise credentials_exception from None

    db = next(get_db_session())
    try:
        user = _get_user_by_username(db, username)

        if user.disabled:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="User account is disabled",
            )

        return user
    except ValueError:
        raise credentials_exception from None
    finally:
        db.close()


# Type alias for WebSocket authentication
WebSocketUser = Annotated[User, Depends(get_websocket_user)]
