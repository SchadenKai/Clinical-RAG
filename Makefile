setup-dev:
	cd backend && uv sync --all-extras && playwright install

run-dev-frontend:
	cd frontend && npm run dev

run-containers:
	cd deployment && docker compose up -d --build --force-recreate

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