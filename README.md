<!-- Badges -->

![Python](https://img.shields.io/badge/python-3.13%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async-green)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

# Backend - NoDesk - Pro4tech (API Fatec)

Backend API for the 6th semester project at FATEC São José dos Campos.

---

## Features

* ⚡ **FastAPI** with async SQLAlchemy (PostgreSQL)
* 🔐 **Argon2id** password hashing + **JWT** issuance
* 🧪 Fully async tests (pytest + httpx + lifespan manager)
* 🧹 Code quality: **ruff** + **pre-commit**
* 🗄️ Database migrations via **Alembic**
* 👤 Optional **admin bootstrap** on startup via `ADMIN_*` env vars

---

## Stack

* Python 3.13+
* FastAPI + Uvicorn
* SQLAlchemy (async) + PostgreSQL (psycopg)
* Pydantic & pydantic-settings
* Alembic
* Pytest, httpx
* Ruff, pre-commit

---

## Project layout (high level)

```
nodesk/
  __init__.py            # FastAPI app + dependency wiring (lifespan)
  authentication/        # token issuer, password hasher, auth routes, protocols
  core/                  # settings, database engine/session, DI helper
  users/                 # user model, routers, schemas, protocols
tests/                   # async API tests and fixtures
```

---

## Setup

The `.env` file holds configuration (secrets, database URI, admin bootstrap, etc.).

### 0) Install pyenv, pipx

### 1) Create and activate the virtualenv, install deps

Windows (PowerShell):

```powershell
poetry config virtualenvs.in-project true
poetry install
cp .env.example .env
.venv\Scripts\activate.ps1
```

Linux / macOS:

```bash
poetry config virtualenvs.in-project true
poetry env use "$(pyenv which python)"  # optional if you use pyenv
poetry install
cp -n .env.example .env
source .venv/bin/activate
```

### 2) Install pre-commit hooks

```bash
pre-commit install
pre-commit install --hook-type commit-msg --hook-type pre-commit
```

### 3) Generate an APP secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Copy it into `.env` as `APP_SECRET`.

On app startup, if `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set and the email does not exist yet, the app will create an active admin user.

---

## Database

### PostgreSQL locally (Linux)

```bash
sudo -u postgres psql
```

In the `psql` prompt:

```sql
-- Create role
CREATE USER nodesk WITH ENCRYPTED PASSWORD 'nodesk';

-- Create database owned by that role
CREATE DATABASE nodesk OWNER nodesk;

-- Exit
\q
```

### Migrations

Apply the migrations to the current database:

```bash
alembic upgrade head
```

Create a new migration after model changes:

```bash
alembic revision --autogenerate -m "describe change"
```

---

## Development

Run the API with live-reload:

```bash
uvicorn nodesk:app --reload
```

* Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
* Docs (Swagger): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Tests

* Tests are fully async (`pytest`, `httpx.AsyncClient`, `ASGITransport`) and run with lifespan so startup/shutdown logic is covered.
* A dedicated test database / overrides are used so your dev DB won’t be polluted.

Run all tests:

```bash
pytest
```

---

## Code quality

Format:

```bash
ruff format .
```

Lint (autofix with pre-commit on staged files):

```bash
ruff check .
```

---
