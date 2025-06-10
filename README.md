# BPO Operations Management Tool

This repository contains a minimal implementation of the Phase 1 MVP for a BPO Operations Management Tool. It is built with **FastAPI** and uses an in-memory data store. The focus is on demonstrating the basic workflow management features.

## Features

- User authentication using OAuth2 and JWT tokens.
- Admin endpoint to create users.
- Project and batch creation with status tracking.
- Operators can start and stop timers on batches to log their work time and item counts.

## Running the server

Install the dependencies and run the FastAPI server from the project root:

```bash
pip install fastapi uvicorn[standard] python-jose[cryptography] passlib[bcrypt]
cd path/to/bpo_data_entry
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` and the interactive docs can be accessed at `/docs`.

A default administrator account is created automatically with username `admin` and password `admin123`. Use these credentials to log in and create additional users.

This is an MVP using an in-memory database and is not meant for production use.

## Configuration

The application reads several environment variables using `pydantic-settings`:

- `SECRET_KEY` - secret used to sign JWT tokens.
- `DATABASE_URL` - connection string for the database.
- `APP_ENV` - name of the environment (e.g. `development` or `production`).

You can define these variables in a `.env` file for local development or set them in your deployment environment.
