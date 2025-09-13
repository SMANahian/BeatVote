.PHONY: run dev format lint test

run:
	FLASK_APP=partyqueue.app flask run

dev:
	FLASK_APP=partyqueue.app FLASK_ENV=development flask run --reload

format:
	black .

lint:
	flake8 partyqueue tests

test:
	pytest
