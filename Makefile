setup-dev:
	cd backend && uv sync --all-extras && playwright install

run-backend-tests:
	make setup-dev && uv run pytest

migrate:
	cd backend && uv run alembic upgrade head

migration:
	cd backend && uv run alembic revision --autogenerate -m "$(m)"

run-containers:
	cd deployment && docker compose up -d --build --force-recreate

run-watch:
	cd deployment && docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build --force-recreate --watch

run-vectors-db:
	cd deployment && docker compose -f docker-compose.milvus.yml up -d

build-images:
	cd backend && docker build -t schadenkai/cdc-who-rag-system:latest .

push-image:
	make build-images
	docker push schadenkai/cdc-who-rag-system:latest

run-backend-docker:
	make build-images
	docker run -p 8000:8000 --env-file .env schadenkai/cdc-who-rag-system:latest

# Dagster orchestration (indexing / SDG / eval pipelines).
# Dockerized: brings up Dagster + its infra deps (Postgres, MinIO, Milvus).
# UI at http://localhost:3333
run-dagster:
	cd deployment && docker compose -f docker-compose.yml -f docker-compose.dagster.yml up -d --build dagster

stop-dagster:
	cd deployment && docker compose -f docker-compose.yml -f docker-compose.dagster.yml stop dagster

# Host-run Dagster dev (no container). Needs Postgres/MinIO/Milvus reachable on
# their localhost ports first (e.g. `make run-containers` or `make run-vectors-db`).
dagster-dev:
	cd backend && uv run dagster dev

# Materialize the full pipeline headlessly (host). Same infra prerequisites.
run-pipelines:
	cd backend && uv run dagster job execute -j rag_pipeline_job