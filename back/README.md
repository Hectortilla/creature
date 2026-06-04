# Creature Card Game API

A FastAPI backend for the Creature Card Game, using **SQLModel** (combining SQLAlchemy ORM + Pydantic) with PostgreSQL.

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL database
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
# Install dependencies
make install
# or
uv sync
```

### Database Configuration

Create a `.env` file in the `back` directory with your PostgreSQL connection string:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/creature
```

### Running the Server

```bash
make run
# or
uv run fastapi dev app/main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Elements
- `GET /elements` - Get all elements
- `GET /elements/{value}` - Get element by ID or label
- `POST /elements` - Create element
- `DELETE /elements/{id}` - Delete element

### Types
- `GET /types` - Get all types
- `GET /types/{value}` - Get type by ID or label
- `POST /types` - Create type
- `DELETE /types/{id}` - Delete type

### Characters
- `GET /characters` - Get all characters
- `GET /characters/{value}` - Get character by ID or label
- `POST /characters` - Create character
- `DELETE /characters/{id}` - Delete character

### Attacks
- `GET /attacks` - Get all attacks
- `GET /attacks/{value}` - Get attack by code or name
- `POST /attacks` - Create attack
- `DELETE /attacks/{id}` - Delete attack

### Abilities
- `GET /abilities` - Get all abilities
- `GET /abilities/{value}` - Get ability by code or name
- `POST /abilities` - Create ability
- `DELETE /abilities/{id}` - Delete ability

### Associations
- `GET /associations` - Get all associations
- `GET /associations/{value}` - Get association by code or name
- `POST /associations` - Create association
- `DELETE /associations/{id}` - Delete association

### Cards
- `GET /cards` - Get all cards
- `GET /cards/{value}` - Get card by code, handle, or name
- `GET /cards/by-attack/{code}` - Get cards by attack
- `GET /cards/by-ability/{code}` - Get cards by ability
- `GET /cards/by-association/{code}` - Get cards by association
- `POST /cards` - Create card
- `DELETE /cards/{id}` - Delete card

### WebSocket
- `WS /game/ws?token=<jwt>&deck_id=<id>[&room_id=<id>]` - Real-time game connection

## Project Structure

```
back/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application entry point
│   ├── config.py         # Configuration settings
│   ├── database.py       # Database connection and session
│   ├── models/           # SQLModel models (ORM + Pydantic combined)
│   │   ├── __init__.py
│   │   ├── ability.py    # Ability, AbilityCreate, AbilityRead
│   │   ├── association.py
│   │   ├── attack.py
│   │   ├── card.py
│   │   ├── character.py
│   │   ├── element.py
│   │   └── type.py
│   ├── services/         # Business logic and CRUD operations
│   │   ├── __init__.py
│   │   ├── abilities.py
│   │   ├── associations.py
│   │   ├── attacks.py
│   │   ├── cards.py
│   │   ├── characters.py
│   │   ├── elements.py
│   │   ├── types.py
│   │   └── utils.py
│   └── routers/          # API route handlers
│       ├── __init__.py
│       ├── abilities.py
│       ├── associations.py
│       ├── attacks.py
│       ├── cards.py
│       ├── characters.py
│       ├── elements.py
│       └── types.py
├── Makefile
├── pyproject.toml
└── README.md
```

## SQLModel Pattern

This project uses SQLModel, which unifies SQLAlchemy ORM and Pydantic into single model definitions:

```python
from sqlmodel import SQLModel, Field

# Base model with shared fields
class ElementBase(SQLModel):
    label: str
    icon: str | None = None

# Request body model
class ElementCreate(ElementBase):
    pass

# Database table model (ORM)
class Element(ElementBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

# Response model
class ElementRead(ElementBase):
    id: int
```

This approach:
- Eliminates code duplication between Pydantic and SQLAlchemy models
- Provides type safety and automatic validation
- Generates accurate OpenAPI documentation
