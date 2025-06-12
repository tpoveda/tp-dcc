# Makefile for tp-core

install:
	uv pip install .[dev]

format:
	ruff check . --fix

lint:
	ruff check .

typecheck:
	mypy tp/

test:
	pytest

check: lint typecheck test