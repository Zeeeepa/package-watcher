.PHONY: install backend frontend dev lint test typecheck build clean

install:
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -e .[dev]
	cd frontend && npm install

backend:
	cd backend && . .venv/bin/activate && python -m app.main

frontend:
	cd frontend && npm run dev

dev:
	@echo "Run 'make backend' and 'make frontend' in separate terminals"

lint:
	cd backend && . .venv/bin/activate && python -m ruff check app tests
	cd frontend && npm run lint

typecheck:
	cd frontend && npm run typecheck

test:
	cd backend && . .venv/bin/activate && python -m pytest tests/ -q

build:
	cd frontend && npm run build

clean:
	rm -rf backend/.venv frontend/node_modules frontend/dist
	find . -type d -name __pycache__ -exec rm -rf {} +
