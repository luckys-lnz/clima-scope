.PHONY: help install install-dev run test clean migrate upgrade downgrade

help:
	@echo "Clima-scope Backend API - Makefile"
	@echo "===================================="
	@echo ""
	@echo "Available targets:"
	@echo "  make venv          - Create virtual environment"
	@echo "  make install       - Install base dependencies"
	@echo "  make install-dev   - Install with development dependencies"
	@echo "  make run           - Run development server"
	@echo "  make test          - Run tests"
	@echo "  make migrate       - Create new database migration"
	@echo "  make upgrade       - Apply database migrations"
	@echo "  make downgrade     - Rollback database migration"
	@echo "  make clean         - Remove virtual environment and build files"
	@echo "  make help          - Show this help message"
	@echo ""

venv:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

install:
	@echo "Installing dependencies..."
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt
	@echo "Installation complete!"

install-dev: install
	@echo "Installing development dependencies..."
	pip install -r requirements-dev.txt
	@echo "Development setup complete!"

run:
	@echo "Starting development server..."
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	@echo "Running tests..."
	pytest tests/ -v

migrate:
	@echo "Creating new migration..."
	@read -p "Migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

upgrade:
	@echo "Applying database migrations..."
	alembic upgrade head

downgrade:
	@echo "Rolling back database migration..."
	alembic downgrade -1

clean:
	@echo "Cleaning up..."
	rm -rf venv/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf __pycache__
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete!"
