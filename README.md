# BPO Operations Management Tool

This repository contains a minimal implementation of a BPO Operations Management Tool. It is built with **FastAPI** and uses an in-memory data store. The project currently implements features from Phases 1 and 2 of the development plan.

## Features

- User authentication using OAuth2 and JWT tokens.
- Admin endpoints to create, edit, and deactivate users.
- Project and batch creation with status tracking.
- Operators can start and stop timers on batches to log their work time and item counts.
- Managers can assign operators to batches and create work shifts.
- A simple dashboard aggregates productivity metrics.
- Validation errors can be logged against a batch and operator.

## Running the server

Install the dependencies and run the FastAPI server from the project root:

```bash
pip install -r requirements.txt
cd path/to/bpo_data_entry
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` and the interactive docs can be accessed at `/docs`.

A default administrator account is created automatically with username `admin` and password `admin123`. Use these credentials to log in and create additional users.

The requirements pin `bcrypt==3.2.0` to avoid a compatibility issue with Passlib on some systems.

This is an MVP using an in-memory database and is not meant for production use.
