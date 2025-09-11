<!-- Badges -->
![Python](https://img.shields.io/badge/python-3.13%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async-green)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

# Backend - NoDesk - Pro4tech (API Fatec)

API backend repository for the 6th Semester of the Database course at FATEC - São José dos Campos

<br>

## Stack

* **Python** 3.13+
* **FastAPI** + **Uvicorn**
* **pydantic-settings** (config via env/.env)
* **pytest**, **httpx** (tests)
* **ruff**, **pre-commit** (code quality)

<br>

## Installation

The `.env` file contains configuration variables (keys, database, etc.). Copy the `.env.example` and adjust as needed.

### 1. Install and prepare the environment:

**Windows:**
```powershell
poetry config virtualenvs.in-project true
poetry install
cp .env.example .env
.venv\Scripts\activate.ps1
```

**Linux/macOS:**
```bash
poetry config virtualenvs.in-project true
poetry install
cp -n .env.example .env
source .venv/bin/activate
```

### 2. Install pre-commit hook:

```bash
pre-commit install
```

#### 2.1. Pre-commit activation:
```bash
pre-commit install --hook-type commit-msg --hook-type pre-commit
```

### 3. Generate an APP_SECRET:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

<br>

## Running in development

```bash
uvicorn nodesk:app --reload --port 8000
```

* Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
* Docs (Swagger): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

<br>

## Tests (async + fixture)

* Tests use `httpx.AsyncClient` with `ASGITransport`, via **fixture** (`tests/conftest.py`).


```bash
pytest
```

<br>

## Code Quality

#### 1. Format:

```bash
ruff format .
```

#### 2. Lint (with autofix via pre-commit):

```bash
ruff check .
```
