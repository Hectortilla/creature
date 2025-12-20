from typing import Annotated

from fastapi import Depends
from sqlmodel import SQLModel, create_engine, Session

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, echo=True)


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def get_db_session():
    """Dependency to get database session."""
    with Session(engine) as session:
        yield session


# Type alias for injecting database session
DBSessionDep = Annotated[Session, Depends(get_db_session)]
