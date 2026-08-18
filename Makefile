.PHONY: up down logs test lint seed
up:
	docker compose up --build
down:
	docker compose down
logs:
	docker compose logs -f
test:
	docker compose run --rm api pytest -q
lint:
	docker compose run --rm api ruff check app tests
seed:
	docker compose run --rm api python -m app.seed
