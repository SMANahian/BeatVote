# PartyQueue

PartyQueue is a Flask + MongoDB + Socket.IO web application for running collaborative karaoke or party music rooms. Users can search YouTube, add songs to a shared queue and vote in real time.

## Features

- Email/password authentication with Flask-Login
- Guest access via cookies
- Realtime queue and chat powered by Socket.IO
- YouTube Data API search proxy
- MongoDB for persistence

## Setup

1. Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in values. Obtain a YouTube Data API v3 key from Google Cloud Console and enable the API.

3. Run MongoDB locally or use the included docker compose configuration:

```bash
docker-compose up
```

4. Start the development server:

```bash
make dev
```

Navigate to [http://localhost:5000](http://localhost:5000) to access the app.

## Testing

Unit tests cover queue ordering, vote logic and room permissions:

```bash
make test
```

## Makefile Targets

- `make run` – start server
- `make dev` – development mode with reload
- `make format` – run black
- `make lint` – run flake8
- `make test` – run pytest

## Docker

The `docker-compose.yml` file defines services for the Flask app and MongoDB. This is suitable for local development.

## Notes

Playback uses the YouTube IFrame Player API and requires a user gesture on the host page to enable audio because of browser autoplay policies.
