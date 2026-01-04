from typing import Annotated, TYPE_CHECKING

from fastapi import Depends, HTTPException, status, Query, WebSocket, WebSocketException
from fastapi.security import OAuth2PasswordBearer

from app.database import DBSessionDep, get_db_session
from app.models.db.user import User
from app.models.schemas.user import TokenData
from app.auth.security import decode_access_token

if TYPE_CHECKING:
    from app.services.users import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSessionDep,
) -> User:
    """Dependency to get the current authenticated user from JWT token."""
    # Lazy import to avoid circular dependency
    from app.services.users import UserService
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str | None = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    token_data = TokenData(username=username)
    
    user = UserService(db).get_by_username(token_data.username)
    if user is None:
        raise credentials_exception
    
    return user


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
    # Lazy import to avoid circular dependency
    from app.services.users import UserService
    
    credentials_exception = WebSocketException(
        code=status.WS_1008_POLICY_VIOLATION,
        reason="Could not validate credentials",
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str | None = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    # Get database session
    db = next(get_db_session())
    try:
        user = UserService(db).get_by_username(username)
        if user is None:
            raise credentials_exception
        
        if user.disabled:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="User account is disabled",
            )
        
        return user
    finally:
        db.close()


# Type alias for WebSocket authentication
WebSocketUser = Annotated[User, Depends(get_websocket_user)]
