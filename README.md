# RefGen AI Backend

RefGen AI is a FastAPI-based backend that automates the creation of academic essays and reference documents.  
It orchestrates OpenAI-powered agents that generate plan outlines, write the content for every section, and produce a formatted DOCX file ready for submission.

## Features
- FastAPI REST API with JWT authentication and profile management.
- Essay planning endpoint that splits the requested page count between introduction, chapters, conclusion, and references.
- Celery worker that asks OpenAI (via LangChain) to write every section with the required volume.
- DOCX exporter that assembles a title page, TOC, generated text, and bibliography using `python-docx`.
- PostgreSQL storage for essays, chapters, and metadata with async SQLAlchemy sessions.

## Tech Stack
- **Framework:** FastAPI, Pydantic v2
- **Database:** PostgreSQL + SQLAlchemy (async and sync engines)
- **Background jobs:** Celery + RabbitMQ
- **AI integration:** LangChain + OpenAI Chat API
- **Docs output:** python-docx

## Prerequisites
- Python 3.11+
- PostgreSQL 14+ with a database created for the app
- RabbitMQ (or compatible AMQP broker)
- OpenAI API key with access to the configured model
- RSA keypair for JWT (`certs/jwt-private.pem`, `certs/jwt-public.pem`)

## Setup
```bash
git clone <repo-url>
cd refgen_ai/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration
Create a `.env` file in the project root (see `.env` for reference). Key variables:

| Variable | Description |
| --- | --- |
| `DB_USER`, `DB_PASS`, `DB_HOST`, `DB_PORT`, `DB_NAME` | PostgreSQL connection |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Celery broker/backend (RabbitMQ by default) |
| `OPENAI_API_KEY`, `MODEL_NAME`, `TEMPERATURE` | OpenAI credentials and model setup |
| `CHARS`, `FULL_CHARS`, `WORDS` | Per-page metrics used to convert pages into character limits |
| `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRES_MINUTES`, `REFRESH_TOKEN_EXPIRES_DAYS` | Auth config |
| `SAVE_DIR` | Directory where generated DOCX files are stored (defaults to `saved_docs/`) |

> The app expects RSA keys under `certs/`. Generate them if you plan to issue tokens locally:
> ```bash
> openssl genrsa -out certs/jwt-private.pem 2048
> openssl rsa -in certs/jwt-private.pem -pubout -out certs/jwt-public.pem
> ```

## Running the services
Start your infrastructure (PostgreSQL, RabbitMQ), then launch the API and worker:

```bash
# Run FastAPI with Uvicorn
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal (same virtualenv)
celery -A src.celery_app.celery_app worker --loglevel=info
```

`src.main` calls `init_db()` on startup, so tables are auto-created based on the SQLAlchemy models.

## Typical workflow
1. **Authenticate & fill profile** – most endpoints require `Authorization: Bearer <token>` and a complete profile (name, university, city, etc.).
2. **Generate a plan**
    ```http
    POST /api/v1/essays/plan/generate
    {
      "topic": "Программирование",
      "checked_by": "Учитель информатики",
      "subject": "Информатика",
      "page_count": 20,
      "chapters_count": 6,
      "language": "ru"
    }
    ```
    The backend distributes pages across sections, stores the plan, and returns the `essay_id`.
3. **Trigger content generation**
    ```http
    POST /api/v1/essays/{essay_id}/generate
    ```
    Celery picks up the job, calls the OpenAI agents, and fills the essay record.
4. **Poll status**
    ```http
    GET /api/v1/essays/{essay_id}/status
    ```
    Wait until the status becomes `GENERATED`.
5. **Download the DOCX**
    ```http
    GET /api/v1/refprint/{essay_id}
    ```
    The first request renders and caches a DOCX file under `saved_docs/`.

## Project structure
```
src/
├── auth/                # JWT auth, user services
├── routes/              # FastAPI routers (essay, refprint, profile)
├── refagent/            # OpenAI agents and helpers
├── refprint/            # DOCX builder utilities
├── tasks/               # Celery tasks (essay generation)
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
└── main.py              # FastAPI entrypoint
```

## Development notes
- Run `ruff`/`black` (if added later) before committing to keep style consistent.
- Tests are not included; when adding features, prefer writing pytest suites under `tests/`.
- Long-running OpenAI calls happen inside Celery; keep API endpoints async and lightweight.
