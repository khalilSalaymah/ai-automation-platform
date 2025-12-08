.PHONY: install test run dev

install:
	pip install -e .

test:
	pytest

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

dev:
	uvicorn app.main:app --reload --port 8083

