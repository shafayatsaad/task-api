# Task API

A small SQLite-backed CRUD API built with FastAPI.

## Tech Stack

- Python
- FastAPI
- SQLite
- Uvicorn

## Database

This project uses SQLite for persistent task storage.

The database file is:

`tasks.db`

It is created automatically when the application starts.

The `tasks` table contains:

| Column | Type    | Description       |
| ------ | ------- | ----------------- |
| id     | INTEGER | Primary key       |
| title  | TEXT    | Task title        |
| done   | BOOLEAN | Completion status |

The application automatically inserts three example tasks only when the database is empty.

## Run the Project

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the server:

```bash
uvicorn main:app --reload
```

Open Swagger:

[http://localhost:8000/docs](http://localhost:8000/docs)

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

## Example SQL

```sql
SELECT * FROM tasks;
```

This query returns all tasks stored in the SQLite database.

## SQL Practice

You can run SQL directly against the database to verify the data. Open a terminal in the project directory and use Python's built-in `sqlite3` module:

```bash
python -c "import sqlite3; print(sqlite3.connect('tasks.db').execute('SELECT * FROM tasks').fetchall())"
```

Or use the interactive shell:

```bash
python -c "import sqlite3; c = sqlite3.connect('tasks.db'); [print(r) for r in c.execute('SELECT * FROM tasks')]"
```

### Useful queries

```sql
-- List all tasks
SELECT * FROM tasks;

-- Only completed tasks
SELECT * FROM tasks WHERE done = 1;

-- Only open tasks
SELECT * FROM tasks WHERE done = 0;

-- Search by title
SELECT * FROM tasks WHERE LOWER(title) LIKE '%milk%';

-- Count tasks
SELECT COUNT(*) FROM tasks;

-- Task statistics
SELECT
    COUNT(*) AS total,
    SUM(CASE WHEN done = 1 THEN 1 ELSE 0 END) AS done
FROM tasks;
```

## Persistence

Unlike the original in-memory implementation, tasks now survive server restarts because they are stored in `tasks.db`.

## Swagger UI

![Swagger UI](task-api.png)
