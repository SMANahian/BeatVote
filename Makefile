.PHONY: run dev format lint test

run:
flask run

dev:
FLASK_ENV=development flask run --reload

format:
black .

lint:
flake8 partyqueue tests

test:
pytest
