# BPO Operations Management Tool

This repository contains a minimal implementation of a BPO Operations Management Tool. It is built with **FastAPI** and uses an in-memory data store. The project currently implements features from Phases 1-3 of the development plan.

## Features

- User authentication using OAuth2 and JWT tokens.
- Admin endpoints to create, edit, and deactivate users.
- Project and batch creation with status tracking.
- Operators can start and stop timers on batches to log their work time and item counts.
- Managers can assign operators to batches and create work shifts.
- A simple dashboard aggregates productivity metrics.
- Validation errors can be logged against a batch and operator with categorized error types.
- Issue tracking allows operators to flag documents for manager review.
- Managers can create knowledge base articles searchable by all users.
- An analytics endpoint reports error rates, performance trends, and cost estimates.
- A monthly CSV performance report can be generated.
- Role-based permissions restrict actions by user role.
- API keys enable integration endpoints for batch import and work-hour export.
- Audit logs record critical actions and can be viewed by admins.
- A basic client portal exposes project status when accessed with an API key.
- An improved web interface at `/ui` uses Bulma for a SaaS-like experience.
  After logging in, users can manage projects and batches directly from the page.

## Running the server

Install the dependencies and run the FastAPI server from the project root:

```bash
pip install -r requirements.txt
cd path/to/bpo_data_entry
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` and the interactive docs can be accessed at `/docs`.
For a simple built-in interface, open `http://localhost:8000/ui` after starting the server. The page now includes a responsive layout similar to SaaS tools like **kintone**.

A default administrator account is created automatically with username `admin` and password `admin123`. Use these credentials to log in and create additional users.

The requirements pin `bcrypt==3.2.0` to avoid a compatibility issue with Passlib on some systems.

This is an MVP using an in-memory database and is not meant for production use.
