.PHONY: help install install-dev install-anthropic venv setup test clean

help:
	@echo "Clima-scope PDF Generator - Makefile"
	@echo "===================================="
	@echo ""
	@echo "Available targets:"
	@echo "  make venv          - Create virtual environment"
	@echo "  make setup         - Full setup (venv + install)"
	@echo "  make install       - Install package and dependencies"
	@echo "  make install-dev   - Install with development dependencies"
	@echo "  make install-anthropic - Install with Anthropic support"
	@echo "  make test          - Run tests"
	@echo "  make clean         - Remove virtual environment and build files"
	@echo "  make help          - Show this help message"
	@echo ""

venv:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

setup: venv
	@echo "Running full setup..."
	./setup_venv.sh
	@echo ""
	@echo "Setup complete! Activate with: source venv/bin/activate"

install:
	@echo "Installing dependencies..."
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt
	pip install -e .
	@echo "Installation complete!"

install-dev: install
	@echo "Installing development dependencies..."
	pip install -r requirements-dev.txt
	@echo "Development setup complete!"

install-anthropic: install
	@echo "Installing Anthropic dependencies..."
	pip install -r requirements-anthropic.txt
	@echo "Anthropic support installed!"

test:
	@echo "Running tests..."
	pytest tests/ -v

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
