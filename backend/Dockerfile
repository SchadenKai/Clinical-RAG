# stage 1: builder
FROM python:3.13.11-slim-bookworm AS builder


COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

# stage 2: runner
FROM python:3.13.11-slim-bookworm AS runner

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

COPY app ./app

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