## Project overview

**Clinical-RAG** is a production-grade, citation-backed AI system that bridges the "Trust Gap" in medical information retrieval. It provides clinicians and public health professionals with a verifiable, real-time interface to the latest **CDC** and **WHO** technical guidelines via an agentic RAG pipeline with an AG-UI chat frontend.

## Tech stack

### Frontend (`/frontend`)
- **Next.js 16** (App Router) / React 19 / TypeScript 5
- **ShadcnUI** (Radix primitives) + **TailwindCSS v4** for styling
- **TanStack React Query** for server-state & data fetching
- **Framer Motion** for animations

### Backend (`/backend`)
- **Python 3.13** / **FastAPI** (standard extras)
- **uv** for package management (see `pyproject.toml`)
- **LangChain** + **LangGraph** for LLM orchestration, RAG pipeline, and multi-agent workflows
- **SQLAlchemy** + **Alembic** for ORM & migrations
- **Pydantic Settings** for config (`.env`-driven, see `app/core/config.py`)

### Databases & infra (`/deployment`)
- **Milvus** — vector DB for RAG (stack defined in `docker-compose.milvus.yml`)
- **PostgreSQL** — relational DB (Alembic migrations in `backend/alembic/`)
- **MinIO** — S3-compatible blob storage for document files

## Commands

### Root (Makefile)
```bash
make setup-dev            # Install backend deps + Playwright
make run-dev-frontend     # Start Next.js dev server
make run-containers       # docker compose up all services
make run-vectors-db       # Start Milvus stack only
make build-images         # Build backend Docker image
```

### Frontend (run from `/frontend`)
```bash
npm run dev       # Dev server
npm run build     # Production build
npm run lint      # ESLint
```

### Backend (run from `/backend`)
```bash
uv sync --all-extras          # Install deps & create venv
uv run fastapi dev            # Dev server (hot-reload)
uv run fastapi run ./app/main.py  # Production
uv run pytest                 # Run tests (pytest + coverage)
uv add <package>              # Add a dependency
```

## Project structure

### Backend — `backend/app/`
| Directory | Purpose |
|---|---|
| `core/` | App config (`config.py`), database engine, security utils |
| `routes/v1/` | **API route handlers** — versioned (v1). Bootstrap in `routes/v1/main.py` |
| `routes/dependencies/` | FastAPI dependency-injection factories (DB sessions, auth, services) |
| `services/` | **Business logic** layer (chat, RAG, scraping, catalog, settings, LLM clients) |
| `agent/` | LangGraph agent graphs — `chat/`, `indexing/`, `react_agent/`, `retriever/` |
| `rag/` | Low-level RAG utilities — chunker, embeddings, vector DB client, retrieval |
| `models/` | SQLAlchemy ORM models |
| `schemas/` | Pydantic request/response schemas |
| `data/` | Static data sources & web source configs |
| `scripts/` | One-off utility scripts |

### Backend Tests — `backend/tests/`
| Directory | Purpose |
|---|---|
| `api/` | Integration tests for API routes (mirrors `app/routes/`) |
| `app/` | Unit and integration tests for services, RAG, and agents (mirrors `app/services/`, `app/rag/`, etc.) |
| `data/` | Tests for web sources and data ingestion (mirrors `app/data/`) |

> The `backend/tests/` directory structure is designed to mirror the `backend/app/` structure for consistent mapping between code and tests.

### Frontend — `frontend/src/`
| Directory | Purpose |
|---|---|
| `app/` | Next.js App Router pages — route groups: `(admin)`, `(auth)`, `(chat)` |
| `components/` | Reusable UI — sub-folders: `chat/`, `documents/`, `layout/`, `ui/` (ShadcnUI) |
| `hooks/` | Custom React hooks (e.g., `use-chat-session`, `use-catalog`, `use-settings`) |
| `lib/` | Utilities, API client (`api-client.ts`), constants, AG-UI agent config |

## Code style & conventions

### Frontend
- Functional components only; hooks for state & side effects
- **Container-presentation pattern** — separate data-fetching containers from pure presentational components
- TypeScript strict mode; create a `types.ts` file per component/feature
- Use ShadcnUI components from `components/ui/`; extend via `class-variance-authority`
- Use TailwindCSS v4 classes for styling; combine with `cn()` utility from `lib/utils.ts`

### Backend
- **API → Services → Repository** layered pattern
  - Routes call services; services call repositories/ORM/external clients
  - Do NOT put business logic directly in route handlers
- FastAPI **dependency injection** via `routes/dependencies/` for all shared resources
- Config via `pydantic-settings` — all env vars defined in `app/core/config.py`
- Linting: **ruff** (rules: E, F, I, B). Type-checking: **mypy** (strict)
- Logging: use `structlog` via `app/logger.py`

## Design patterns (backend)

### Lazy singleton (`@property`)
For clients that connect to a **single external service** (one provider, one connection), use a class with a private `_client` field and a `@property` that lazily initializes it on first access. This avoids creating connections at import time and ensures one instance per object.

**Use for:** Milvus (`VectorClient`), MinIO/S3 (`S3Service`)

```python
class SomeClient:
    def __init__(self, settings: Settings):
        self._client: ActualClient | None = None
        self.settings = settings

    @property
    def client(self) -> ActualClient:
        if self._client is None:
            self._client = ActualClient(...)
        return self._client
```

### Singleton + factory (`@property` with provider branching)
For clients that support **multiple providers** (e.g., OpenAI vs Gemini vs Anthropic), apply the same lazy `@property` pattern but add provider-based branching inside. The provider is passed at construction time; the `client` getter acts as an inline factory.

**Use for:** LLM chat models (`ChatModelService` in `services/llm/factory.py`), embeddings (`EmbeddingService` in `rag/embeddings.py`)

```python
class MultiProviderService:
    def __init__(self, provider: str, config: dict):
        self._client: BaseClient | None = None
        self.provider = provider
        self.config = config

    @property
    def client(self) -> BaseClient:
        if self._client is None:
            if self.provider == "openai":
                self._client = OpenAIClient(**self.config)
            elif self.provider == "gemini":
                self._client = GeminiClient(**self.config)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
        return self._client
```

### Dependency caching (`@lru_cache`)
FastAPI dependency functions in `routes/dependencies/` are decorated with `@lru_cache` so they return the **same instance** for the lifetime of the process. This is the glue that makes the singletons above application-scoped.

```python
@lru_cache
def get_some_service(settings: Annotated[Settings, Depends(get_app_settings)]) -> SomeService:
    return SomeService(settings)
```

> When adding a new external client or multi-provider service, follow the matching pattern above and create a corresponding `@lru_cache` dependency in `routes/dependencies/`.

## Testing

### Backend
```bash
uv run pytest                 # All tests with coverage
uv run pytest -m "not slow"   # Skip slow tests
uv run pytest -m integration  # Integration tests only
```
- Tests live in `backend/tests/` — sub-folders: `api/`, `app/`, `data/`
- Coverage config in `pyproject.toml` — currently tracks `app/` package
- Markers: `@pytest.mark.slow`, `@pytest.mark.integration`

## Environment variables

Config is loaded from `.env` at the project root. Key variables:
- `DEV_MODE` — set to `true` to skip LLM/embedding smoke tests on startup
- `LLM_PROVIDER`, `LLM_MODEL_NAME`, `LLM_API_KEY` — LLM config
- `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_API_KEY` — embedding config
- `MILVUS_URL`, `MILVUS_DB_NAME`, `MILVUS_COLLECTION_NAME` — vector DB
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` — PostgreSQL
- `MINIO_ENDPOINT_URL`, `MINIO_USERNAME`, `MINIO_PASSWORD` — MinIO
- `JWT_SECRET` — auth token signing