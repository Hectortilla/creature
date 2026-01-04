from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.database import DBSessionDep
from app.models.schemas.user import Token, UserCreate, UserRead
from app.settings.config import get_settings
from app.auth.security import create_access_token
from app.services.users import UserService
from app.auth.dependencies import CurrentActiveUser

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DBSessionDep,
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = UserService(db).authenticate(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.auth_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires,
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: DBSessionDep,
) -> UserRead:
    """
    Register a new user.
    """
    service = UserService(db)
    
    # Check if username already exists
    if service.get_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Check if email already exists (if provided)
    if user_data.email and service.get_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    user = service.create(user_data)
    return UserRead.model_validate(user)


@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: CurrentActiveUser) -> UserRead:
    """
    Get current authenticated user.
    """
    return UserRead.model_validate(current_user)

