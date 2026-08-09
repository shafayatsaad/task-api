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

## Persistence

Unlike the original in-memory implementation, tasks now survive server restarts because they are stored in `tasks.db`.

## Swagger UI

![Swagger UI](task-api.png)
