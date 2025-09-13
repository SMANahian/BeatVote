# PartyQueue

PartyQueue is a Flask + MongoDB + Socket.IO web application for running collaborative karaoke or party music rooms. Users can search YouTube, add songs to a shared queue and vote in real time.

## Features

- Email/password authentication with Flask-Login
- Guest access via cookies
- Realtime queue and chat powered by Socket.IO
- YouTube Data API search proxy
- MongoDB for persistence

## Setup

### 1. Prerequisites

- Python 3.10+ and `pip`
- [Docker](https://docs.docker.com/get-docker/) (optional, for running MongoDB)
- A Google Cloud project with access to the YouTube Data API v3

### 2. Install dependencies

Create a virtual environment and install the required Python packages:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and set the required values:

```bash
cp .env.example .env
```

- `FLASK_ENV` – development or production mode
- `SECRET_KEY` – random string used by Flask for session security
- `MONGODB_URI` – connection string for MongoDB (e.g. `mongodb://localhost:27017/partyqueue`)
- `YOUTUBE_API_KEY` – API key for the YouTube Data API v3

To obtain a YouTube API key:

1. Visit the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project if necessary.
3. Enable the **YouTube Data API v3** for the project.
4. Create an API key and place it in the `YOUTUBE_API_KEY` field in `.env`.

### 4. Start MongoDB

Run a local MongoDB instance or start it with Docker:

```bash
docker-compose up mongo
```

If you prefer to run the entire stack in Docker, you can run:

```bash
docker-compose up
```

### 5. Launch the development server

```bash
make dev
```

The app will be available at [http://localhost:5000](http://localhost:5000).

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
