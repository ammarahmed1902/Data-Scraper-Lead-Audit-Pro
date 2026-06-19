.PHONY: dev prod down logs migrate test lint

dev:
	docker compose up -d

prod:
	docker compose -f docker-compose.prod.yml up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -m scripts.seed_admin

test-backend:
	cd backend && pytest

test-frontend:
	cd frontend && npm run type-check

lint:
	cd backend && ruff check app tests
	cd frontend && npm run lint

install:
	cd frontend && npm install
	cd backend && pip install -r requirements.txt
