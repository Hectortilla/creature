from sqlmodel import Session, select

from app.models.db import User
from app.models.schemas import UserCreate
from app.auth.security import verify_password, get_password_hash


class UserService:
    """Service for user-related operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_username(self, username: str) -> User | None:
        """Get user by username."""
        return self.db.exec(
            select(User).where(User.username == username)
        ).first()
    
    def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        return self.db.exec(
            select(User).where(User.email == email)
        ).first()
    
    def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        return self.db.exec(
            select(User).where(User.id == user_id)
        ).first()
    
    def create(self, user_data: UserCreate) -> User:
        """Create a new user with hashed password."""
        hashed_password = get_password_hash(user_data.password)
        
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def authenticate(self, username: str, password: str) -> User | None:
        """Authenticate a user by username and password."""
        user = self.get_by_username(username)
        
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        
        return user

