.PHONY: up down logs migrate makemigrations superuser test test-backend test-frontend lint format build

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose run --rm backend python manage.py migrate

makemigrations:
	docker compose run --rm backend python manage.py makemigrations

superuser:
	docker compose run --rm backend python manage.py createsuperuser

test: test-backend test-frontend

test-backend:
	docker compose run --rm backend pytest

test-frontend:
	docker compose run --rm frontend npm test -- --run

lint:
	docker compose run --rm backend ruff check .
	docker compose run --rm backend mypy .
	docker compose run --rm frontend npm run lint
	docker compose run --rm frontend npm run typecheck

format:
	docker compose run --rm backend ruff format .
	docker compose run --rm frontend npm run format

build:
	docker compose build
