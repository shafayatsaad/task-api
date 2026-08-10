# Task API

A small PostgreSQL-backed CRUD API built with FastAPI, runnable with Docker Compose.

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- psycopg
- Docker / Docker Compose

## Architecture

Storage is an implementation detail. The routes never touch SQL directly — they delegate to a repository module, which is the only place that talks to the database.

```text
FastAPI routes
      ↓
task_repository.py
      ↓
database.py
      ↓
PostgreSQL
      ↓
Docker volume
```

This is the storage-swap lesson in practice:

```text
A1: Python list  →  A2: SQLite  →  A3: PostgreSQL
```

The routes (`GET /tasks`, `POST /tasks`, `PUT /tasks/{id}`, `DELETE /tasks/{id}`, ...) did **not** change between A2 and A3 — only the storage implementation did.

## Prerequisites

- Docker with Docker Compose
- Python 3.11+ (only needed to run without Docker)

## Run with Docker Compose

Copy the environment example and adjust if needed:

```bash
cp .env.example .env
```

Start the API and database:

```bash
docker compose up --build
```

The API is available at:

[http://localhost:8000/docs](http://localhost:8000/docs)

### Important: `DATABASE_URL` inside Docker

Inside Compose, the API connects to the `db` service name, **not** `localhost`:

```env
DATABASE_URL=postgresql://postgres:dev@db:5432/tasks
```

The `taskdata` volume persists the data. Containers can be removed and recreated without losing rows:

```bash
docker compose down
docker compose up -d
```

## Run without Docker

Install dependencies:

```bash
pip install -r requirements.txt
```

Requires a PostgreSQL server. Set `DATABASE_URL` in `.env` (default: `postgresql://postgres:dev@localhost:5432/tasks`).

Start the server:

```bash
uvicorn main:app --reload
```

## Configuration

| Variable       | Example                                          | Description                  |
| -------------- | ------------------------------------------------ | ---------------------------- |
| `DATABASE_URL` | `postgresql://postgres:dev@localhost:5432/tasks` | PostgreSQL connection string |

`.env` is gitignored. `.env.example` is committed as a template.

## Database

The `tasks` table is created automatically on startup (see `schema.sql`):

| Column | Type    | Description            |
| ------ | ------- | ---------------------- |
| id     | INTEGER | Primary key (identity) |
| title  | TEXT    | Task title             |
| done   | BOOLEAN | Completion status      |

The application automatically inserts three example tasks only when the table is empty.

## API Endpoints

| Method | Endpoint      | Description         |
| ------ | ------------- | ------------------- |
| GET    | `/`           | API information     |
| GET    | `/health`     | Health check        |
| GET    | `/tasks`      | List tasks          |
| POST   | `/tasks`      | Create task         |
| GET    | `/tasks/{id}` | Get task            |
| PUT    | `/tasks/{id}` | Update task         |
| DELETE | `/tasks/{id}` | Delete task         |
| GET    | `/stats`      | Task statistics     |
| POST   | `/reset`      | Reset example tasks |

### Example

```bash
curl -i http://localhost:8000/tasks
```

Create a task:

```bash
curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk"}'
```

## Persistence Proof

Data survives container removal because it lives in the Postgres volume, not in the container filesystem.

```text
docker compose up
  → POST /tasks {"title":"Persistence test"}
  → GET /tasks  → task exists
docker compose down
docker compose up
  → GET /tasks  → task still exists ✓
```

## SQL Practice

Query the database directly from the API container:

```bash
docker compose exec db psql -U postgres -d tasks -c "SELECT * FROM tasks;"
```

Useful queries:

```sql
-- List all tasks
SELECT * FROM tasks;

-- Only completed tasks
SELECT * FROM tasks WHERE done = TRUE;

-- Search by title
SELECT * FROM tasks WHERE LOWER(title) LIKE '%milk%';

-- Task statistics
SELECT
    COUNT(*) AS total,
    SUM(CASE WHEN done THEN 1 ELSE 0 END) AS done
FROM tasks;
```

## Swagger UI

![Swagger UI](task-api.png)
