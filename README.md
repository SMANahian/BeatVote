# BeatVote

BeatVote is a Flask + MongoDB + React application for running collaborative karaoke / party music rooms. Guests can join with a code, suggest songs from YouTube, and vote the next track to the top.

## Features

- Email/password authentication with Flask-Login
- Guest access via cookies
- Room roles (host / suggestor / listener)
- Queue updates via simple HTTP polling (prototype)
- YouTube Data API search proxy
- MongoDB for persistence
- Optional Chrome/Brave extension player (auto-advance in a dedicated YouTube tab)

## Setup

### 1. Prerequisites

- Python 3.10+
- Node.js 18+ (for the React frontend build)
- [Docker](https://docs.docker.com/get-docker/) (optional, for running MongoDB)
- A Google Cloud project with access to the YouTube Data API v3

### 2. Install dependencies

Create a virtual environment and install the required Python packages:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Install frontend deps (pnpm recommended, but npm works too):

```bash
cd frontend
pnpm install
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and set the required values:

```bash
cp .env.example .env
```

- `FLASK_ENV` – development or production mode
- `SECRET_KEY` – random string used by Flask for session security
- `MONGO_URI` – connection string for MongoDB (e.g. `mongodb://localhost:27017/beatvote`)
  (`MONGODB_URI` is also accepted)
- `YOUTUBE_API_KEY` – API key for the YouTube Data API v3

To obtain a YouTube API key:

1. Visit the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project if necessary.
3. Enable the **YouTube Data API v3** for the project.
4. Create an API key and place it in the `YOUTUBE_API_KEY` field in `.env`.

### 4. Start MongoDB

The application needs access to a running MongoDB server.

#### Option A: Docker

If you have Docker installed you can start a database using the provided
compose file:

```bash
docker-compose up mongo
```

This launches MongoDB on `localhost:27017` and persists data in the
`mongo_data` volume.

#### Option B: Local installation

Alternatively install MongoDB Community Edition natively on your machine by
following the [official installation
guide](https://www.mongodb.com/docs/manual/installation/). Once installed,
start the service. Examples:

```bash
# macOS (Homebrew)
brew tap mongodb/brew
brew install mongodb-community@6.0
brew services start mongodb-community@6.0

# Ubuntu / Debian
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
```

The application expects MongoDB at `mongodb://localhost:27017/beatvote` by
default. You can change this by setting `MONGO_URI` in `.env` (or
`MONGODB_URI`).

If you prefer to run the entire stack in Docker, you can run:

```bash
docker-compose up --build
```

### 5. Build + run

#### Option A (simplest): build the React UI once, serve from Flask

```bash
cd frontend
pnpm build
cd ..
make dev
```

Open `http://127.0.0.1:5000`.

#### Option B: run Vite dev server (proxying `/api` to Flask)

```bash
make dev
```

In another terminal:

```bash
cd frontend
pnpm dev
```

Open `http://127.0.0.1:5173` (recommended over `localhost` so cookies work).

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

## Browser Extension

A Chrome/Brave extension is provided in the `extension` directory. It keeps the host room page pinned and plays queued songs in a dedicated YouTube tab, auto-advancing the queue via a host token.

### Installation

1. Ensure the BeatVote server is running.
2. In Brave, open `brave://extensions`.
3. Enable **Developer mode**.
4. Click **Load unpacked** and select the `extension` folder.
5. Open `http://127.0.0.1:5000/host`, create a room, then open the room’s host view.
6. The host view exposes a Host Token. The extension will auto-sync config from the host tab, or you can paste Server URL + Room ID + Host Token in the extension popup.

## Notes

Playback uses the YouTube IFrame Player API and requires a user gesture on the host page to enable audio because of browser autoplay policies.
