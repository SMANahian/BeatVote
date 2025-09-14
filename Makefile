.PHONY: run dev format lint test

run:
	flask --app partyqueue.app socketio run

dev:
	flask --app partyqueue.app --debug socketio run

format:
	black .

lint:
	flake8 partyqueue tests

test:
	pytest
