# Task API

A small in-memory CRUD API for managing a to-do list. Built with FastAPI for the FlyRank Backend Internship — Week 2 Assignment.

## Run it

```bash
pip install fastapi uvicorn
uvicorn main:app --reload
```

Then visit `http://localhost:8000/docs` for Swagger UI.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| GET | `/tasks` | List all tasks (optional: `?done=true`, `?search=milk`) |
| GET | `/tasks/{id}` | Get one task |
| POST | `/tasks` | Create a task |
| PUT | `/tasks/{id}` | Update a task |
| DELETE | `/tasks/{id}` | Delete a task |
| GET | `/stats` | Task statistics |
| POST | `/reset` | Reset to the 3 example tasks |

## Example curl output

```bash
$ curl -i http://localhost:8000/tasks/1
HTTP/1.1 200 OK
content-type: application/json

{"id":1,"title":"Buy milk","done":false}
```

## The Mortality Experiment

Create a task via `POST /tasks`, restart the server, then `GET /tasks`. The new task disappears and only the 3 original tasks remain. This happens because data lives only in memory (a Python list variable). When the program stops, the variable is wiped. This is exactly why real applications use databases.

## Swagger UI

![Swagger UI](swagger-screenshot.png)
