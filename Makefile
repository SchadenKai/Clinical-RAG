setup-dev:
	cd backend && uv sync --all-extras && playwright install

run-containers:
	cd deployment && docker compose up -d --build --force-recreate

run-vectors-db:
	cd deployment && docker compose -f docker-compose.milvus.yml up -d

push-image:
	cd backend && docker build -t schadenkai/cdc-who-rag-system:latest .
	docker push schadenkai/cdc-who-rag-system:latest