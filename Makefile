.PHONY: help install test run docker-build docker-run clean lint format

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make test          - Run tests"
	@echo "  make run           - Run locally"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run Docker container"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make clean         - Clean temporary files"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v --cov=server --cov-report=html --cov-report=term

run:
	uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker build -t ai-receptionist:latest .

docker-run:
	docker run -p 8000:8000 --env-file .env ai-receptionist:latest

lint:
	flake8 server/ tests/
	mypy server/

format:
	black server/ tests/
	isort server/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build







