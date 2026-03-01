# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup
```bash
# Install dependencies
poetry install

# Configure environment
cp .env.example .env
# Edit .env and set DATABASE_URL to: postgresql://admin:secure_password@localhost:5432/backend
```

### Running the Server
```bash
# Start development server with auto-reload
poetry run uvicorn app.main:app --reload

# Custom host/port
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Server runs at `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Database
```bash
# Start PostgreSQL container (from infrastructure/postgres/)
cd ../../infrastructure/postgres
docker compose up -d

# Stop database
docker compose down

# View logs
docker compose logs -f postgres
```

Database credentials (from docker-compose.yaml):
- Host: localhost:5432
- User: admin
- Password: secure_password
- Database: backend
- Connection URL: `postgresql+asyncpg://admin:secure_password@localhost:5432/backend`

### Database Migrations (Alembic)
```bash
# Create a new migration (auto-generate from model changes)
poetry run alembic revision --autogenerate -m "description of changes"

# Apply all pending migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# Show current migration version
poetry run alembic current

# Show migration history
poetry run alembic history
```

**Important**: When creating new models:
1. Define the model in the appropriate module (e.g., `app/modules/auth/models.py`)
2. Import the model in `app/models/__init__.py` so Alembic can detect it
3. Run `alembic revision --autogenerate` to create the migration
4. Review the generated migration file in `app/alembic/versions/`
5. Apply with `alembic upgrade head`

## Architecture Overview

This backend follows a **Modular Monolith** pattern with a **3-module structure** based on Bounded Contexts:

### Modules & Bounded Contexts

| Module | Bounded Context | Responsibilities |
|--------|----------------|------------------|
| **auth** | Identity & Access Management | Magic Link authentication, JWT tokens, User CRUD, account deletion |
| **quiz** | Content Management | Quiz CRUD, state machine (private/protected/public), ownership, **Task CRUD** (Multiple Choice/Free Text/Cloze), LLM-based task generation |
| **learning** | Learning Progress & Evaluation | **Attempt** CRUD, answer persistence (auto-save), evaluation (MC/Cloze/Free Text), learning statistics |
| **llm** | Infrastructure | LLM provider abstraction, task generation, free text evaluation |

### Key Architectural Decisions

**Why Tasks are in Quiz Module (not separate):**
- Tasks are child entities that cannot exist without a Quiz
- Strong ownership relationship
- Same bounded context (Content Management)

**Why Attempts are in Learning Module (not Quiz):**
- Independent lifecycle from Quiz
- Different business concerns (Content vs. Learning Progress)
- Clear domain boundary: Quiz = "What content exists?", Learning = "How well does the user learn?"

**Module Communication Rules:**
- ✅ `learning` → `quiz` (Read-Only): Learning reads Quiz/Task data
- ✅ `quiz` → `llm`: Quiz uses LLM for task generation
- ✅ `learning` → `llm`: Learning uses LLM for free text evaluation
- ✅ All modules → `auth`: User authentication via CurrentUserId dependency
- ❌ `quiz` MUST NOT depend on `learning`
- ❌ `learning` MUST NOT write to `quiz` (only read!)
- ❌ `auth` MUST NOT depend on other modules (only used by others)

**Cross-Module Access:**
- Only through Service layer
- Repository access only within the module
- No circular dependencies
- Shared logic goes in `core/` or `shared/`

### Layer Architecture

Each module follows a **3-layer architecture**:

**1. Router (API Layer)** - `router.py`
- HTTP endpoints
- Request/Response validation (Pydantic)
- Dependency injection
- Delegates to Service layer
- Flow: `Request → Router → Service → Repository → Database`

**2. Service (Business Logic Layer)** - `service.py` or `services/`
- Business logic orchestration
- Coordinates multiple repositories
- Calls other modules (e.g., LLM service)
- Error handling
- **NO direct HTTP dependencies**

**3. Repository (Data Access Layer)** - `repository.py` or `repositories/`
- Pure database operations (CRUD)
- SQLAlchemy queries
- **NO business logic**

**4. Models (ORM)** - `models.py` or `models/`
- SQLAlchemy table structures
- Relationships

**5. Schemas (DTOs)** - `schemas.py` or `schemas/`
- Pydantic request/response DTOs
- Validation

### Module Structure Patterns

**Small modules** (auth): Flat structure
```
auth/
├── router.py
├── service.py
├── repository.py
├── models.py
└── schemas.py
```

**Large modules** (quiz, learning): Nested structure
```
quiz/
├── router.py
├── services/
│   ├── quiz_service.py
│   └── task_service.py
├── repositories/
│   ├── quiz_repository.py
│   └── task_repository.py
├── models/
│   ├── quiz.py
│   └── task.py
└── schemas/
    ├── quiz.py
    └── task.py
```

## Technology Stack

- **FastAPI**: Web framework
- **SQLAlchemy 2.0**: ORM (async)
- **AsyncPG**: PostgreSQL driver (async)
- **Alembic**: Database migrations (TODO)
- **Pydantic**: Validation & settings
- **PostgreSQL 17**: Database
- **Python-Jose**: JWT authentication (TODO)
- **Passlib**: Password hashing with Bcrypt (TODO)
- **Uvicorn**: ASGI server
- **Poetry**: Dependency management
- **Python 3.13+**: Required version

## Implementation Status

**Completed:**
- Core modules (config, exceptions, database)
- Database session management with `DatabaseSessionManager`
- Shared modules (dependencies with `DBSessionDep`, utils)
- Module structure (auth, quiz, learning, llm)
- FastAPI app with router registration
- Basic health check endpoints for all modules
- Alembic configuration for async SQLAlchemy migrations
- Base model setup with `Base` class

**TODO:**
- Service, repository, model implementations per module
- Security module (JWT, hashing) in app/core/security.py
- Authentication dependencies (CurrentUser, CurrentUserId)
- LLM provider implementations
- Tests
- CI/CD pipeline

## Coding Guidelines

### Database Session Usage

Use the `DBSessionDep` type alias for dependency injection:

```python
# router.py
from app.shared.dependencies import DBSessionDep

@router.post("/quizzes")
async def create_quiz(
    request: QuizCreate,
    db: DBSessionDep,  # Async database session
):
    # Use db session directly or pass to service
    service = QuizService(db)
    return await service.create_quiz(request)
```

### Dependency Injection Pattern
```python
# router.py
@router.post("/quizzes")
async def create_quiz(
    request: QuizCreate,
    db: DBSessionDep,
    user_id: CurrentUserId,  # Dependency (TODO)
):
    service = QuizService(db)
    return await service.create_quiz(request, user_id)

# service.py
class QuizService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = QuizRepository(db)

    async def create_quiz(self, data, user_id):
        quiz = await self.repo.create(data, user_id)
        return quiz
```

### Layer Responsibilities
- **Router**: HTTP handling only, no business logic
- **Service**: Business logic and orchestration
- **Repository**: Database operations only
- **Models**: Database schema only
- **Schemas**: Validation only

### Database Models
- Use SQLAlchemy 2.0 async patterns
- Models inherit from `Base` (from app.core.database)
- Use proper relationships and foreign keys
- Follow PostgreSQL naming conventions

### Environment Configuration
- All settings in `app/core/config.py` using Pydantic Settings
- Load from .env file
- Use `get_settings()` function for cached access
- Never hardcode credentials

## Project Context

This is a university project (SYP) for an AI-powered learning platform. The platform allows:
- Users to create quizzes with different task types (Multiple Choice, Free Text, Cloze)
- LLM-based task generation
- Learning progress tracking through attempts
- Automated evaluation with LLM support for free text answers
