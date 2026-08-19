.PHONY: help install seed backend frontend test lint run-stack dev-demo clean

help:
	@echo "PromptHub Enterprise targets:"
	@echo "  install       Install backend (uv) and frontend (npm) dependencies"
	@echo "  seed          Create the database and load seed data (uses local .env)"
	@echo "  backend       Run the FastAPI backend on :8000"
	@echo "  frontend      Run the Vite dev server on :5173"
	@echo "  dev-demo      One command: seed + backend + frontend (three terminals style)"
	@echo "  test          Run backend pytest suite"
	@echo "  run-stack     Build and start the full docker-compose stack (postgres/qdrant/ollama/backend/frontend)"
	@echo "  lint          Ruff check on backend"
	@echo "  clean         Remove generated data and caches"

install:
	cd backend && uv sync
	cd frontend && npm install

seed:
	cd backend && uv run python -c "from app.seed import seed_all; seed_all()"

backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev-demo:
	@echo "Run 'make seed', then 'make backend' and 'make frontend' in separate terminals."

test:
	cd backend && uv run pytest -q

run-stack:
	docker compose up --build

lint:
	cd backend && uv run ruff check app

clean:
	rm -rf backend/.venv frontend/node_modules data/generated backend/prompthub.db