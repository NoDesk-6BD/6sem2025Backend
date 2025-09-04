<!-- Badges -->
![Python](https://img.shields.io/badge/python-3.13%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async-green)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

# Backend - NoDesk - Pro4tech (API Fatec)

Repositório backend da API para o 6º Semestre do curso de Banco de Dados da FATEC - São José dos Campos

<br>

## Stack

* **Python** 3.13+
* **FastAPI** + **Uvicorn**
* **pydantic-settings** (config via env/.env)
* **pytest**, **httpx** (tests)
* **ruff**, **pre-commit** (qualidade de código)

<br>

## Instalação

O arquivo `.env` contém variáveis de configuração (chaves, banco etc). Copie o `.env.example` e ajuste conforme necessário.

### 1. Instalar e preparar o ambiente:

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

### 2. Instalar pre-commit hook:

```bash
pre-commit install
```

#### 2.1. Ativação do pre-commit:
```bash
pre-commit install --hook-type commit-msg --hook-type pre-commit
```

### 3. Gerar um APP_SECRET:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

<br>

## Executando em desenvolvimento

```bash
uvicorn nodesk:app --reload --port 8000
```

* Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
* Docs (Swagger): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

<br>

## Testes (async + fixture)

* Os testes usam `httpx.AsyncClient` com `ASGITransport`, via **fixture** (`tests/conftest.py`).


```bash
pytest
```

<br>

## Qualidade de Código

#### 1. Formatar:

```bash
ruff format .
```

#### 2. Lint (com autofix via pre-commit):

```bash
ruff check .
```
