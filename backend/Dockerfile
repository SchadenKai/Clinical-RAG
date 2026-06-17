# stage 1: builder
FROM python:3.13.11-slim-bookworm AS builder


COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# stage 2: runner
FROM python:3.13.11-slim-bookworm AS runner

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    DEEPEVAL_TELEMETRY_OPT_OUT=YES \
    DEEPEVAL_UPDATE_WARNING_OPT_IN=NO \
    ERROR_REPORTING=NO

COPY app ./app

# Alembic config + migrations are applied at startup (see app/main.py lifespan)
# and via `make migrate`, so they must be present in the runtime image.
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

RUN apt-get update && \
    apt-get install -y curl &&\
    playwright install-deps && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m appuser && chown -R appuser /app

# set created user as the current user
USER appuser

RUN playwright install

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]