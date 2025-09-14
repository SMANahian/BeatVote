.PHONY: run dev format lint test

run:
	FLASK_APP=beatvote.app flask run

dev:
	FLASK_APP=beatvote.app FLASK_ENV=development flask run --reload

format:
	black .

lint:
	flake8 beatvote tests

test:
	pytest
