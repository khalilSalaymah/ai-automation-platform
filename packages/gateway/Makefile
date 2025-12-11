.PHONY: install run test lint format clean

install:
	pip install -e .

run:
	uvicorn app.main:app --reload --port 8080

test:
	pytest

lint:
	ruff check .
	mypy .

format:
	black .

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
