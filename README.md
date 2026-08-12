# Task API — Auth & Protect

A FastAPI + PostgreSQL CRUD API extended with **Supabase Auth** for secure user authentication and protected routes.

This project completes the Week 4 **Auth - Login & Protect** assignment while preserving the existing Task API from the previous backend work.

## What this project demonstrates

- User signup with Supabase Auth
- User login with email/password
- JWT access-token handling
- Bearer-token verification with `supabase.auth.get_user(token)`
- Reusable FastAPI authentication dependency
- Public vs protected endpoints
- Logout endpoint
- Automatic Swagger UI at `/docs` with Bearer authentication
- Environment variables for credentials
- PostgreSQL-backed task CRUD API

## Architecture

```text
Client
  │
  ├── POST /auth/signup ───────────────┐
  ├── POST /auth/login ────────────────┤
  │                                     ▼
  │                               Supabase Auth
  │                                     │
  │                              JWT access token
  │                                     │
  └── Authorization: Bearer <JWT> ─────▼
                                  FastAPI dependency
                                         │
                              supabase.auth.get_user(token)
                                         │
                                  verified Supabase user
                                         │
                         ┌───────────────┴───────────────┐
                         ▼                               ▼
                /protected/profile             /protected/dashboard
```

The protected routes do not trust the token merely because it exists. The backend sends the token to Supabase `get_user(token)`, which validates the JWT with the Auth server.

## Tech stack

- Python 3.11+
- FastAPI
- Supabase Python SDK
- PostgreSQL
- psycopg
- Docker / Docker Compose

## 1. Configure Supabase

Create or use a Supabase project with Email/Password authentication enabled.

Copy `.env.example` to `.env` and fill in:

```env
DATABASE_URL=postgresql://postgres:dev@localhost:5432/tasks
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=sb_publishable_your_publishable_key
```

**Never commit `.env` or private/service-role keys.** The publishable key is intended for public/client use, but keeping all environment-specific values in `.env` makes the project configuration portable and keeps credentials out of source control.

If your Supabase project requires email confirmation, signup may return a user without a session. Confirm the email before attempting password login, or adjust the project's confirmation setting for local assignment testing.

## 2. Install and run locally

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install packages:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn main:app --reload
```

Open:

- API: http://localhost:8000/
- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

## 3. Run with Docker Compose

Create `.env` first, then:

```bash
docker compose up --build
```

Compose passes `SUPABASE_URL` and `SUPABASE_KEY` into the API container while PostgreSQL runs in the `db` service.

## Authentication API reference

| Method | Endpoint | Auth | Expected success |
|---|---|---:|---|
| POST | `/auth/signup` | No | `201 Created` |
| POST | `/auth/login` | No | `200 OK` |
| POST | `/auth/logout` | Bearer JWT | `204 No Content` |
| GET | `/public/info` | No | `200 OK` |
| GET | `/protected/profile` | Bearer JWT | `200 OK` |
| GET | `/protected/dashboard` | Bearer JWT | `200 OK` |

### Required error behavior

| Situation | Status | Response |
|---|---:|---|
| Missing signup/login fields | `400` | JSON error |
| Invalid login credentials | `401` | `{"error":"Invalid login credentials"}` |
| Missing Authorization header | `401` | `{"error":"Access token required"}` |
| Invalid/expired JWT | `401` | `{"error":"Invalid or expired token"}` |

## 4. Test the authentication flow

### Public route

```bash
curl -i http://localhost:8000/public/info
```

Expected:

```json
{"message":"Welcome stranger! This info is public."}
```

### Protected route without a token

```bash
curl -i http://localhost:8000/protected/profile
```

Expected status: `401`.

### Sign up

Use a test email address:

```bash
curl -i -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"your-test-email@example.com","password":"StrongPassword123!"}'
```

Expected status: `201`.

If email confirmation is enabled in Supabase, confirm the email before login.

### Log in

```bash
curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your-test-email@example.com","password":"StrongPassword123!"}'
```

Copy the returned `access_token`.

### Protected profile with a valid token

```bash
curl -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected status: `200` and verified user information.

### Invalid token test

Change one character in the token and run the same command.

Expected status: `401` with:

```json
{"error":"Invalid or expired token"}
```

### Protected dashboard

```bash
curl -i http://localhost:8000/protected/dashboard \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected status: `200`.

### Logout

```bash
curl -i -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected status: `204`.

> Supabase access JWTs remain valid until their expiry even after sign-out. Logout invalidates the session/refresh-token state; clients should discard the local access and refresh tokens.

## 5. Swagger UI

Open:

```text
http://localhost:8000/docs
```

FastAPI generates the OpenAPI documentation automatically. The protected endpoints expose an **Authorize** button because the authentication dependency uses `HTTPBearer`.

Workflow:

1. Log in using `/auth/login`.
2. Copy `access_token` from the response.
3. Click **Authorize** in Swagger.
4. Paste the JWT into the Bearer authentication field.
5. Click **Authorize**.
6. Use **Try it out** on `/protected/profile` or `/protected/dashboard`.

## Existing Task API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/tasks` | List tasks |
| POST | `/tasks` | Create task |
| GET | `/tasks/{id}` | Get task |
| PUT | `/tasks/{id}` | Update task |
| DELETE | `/tasks/{id}` | Delete task |
| GET | `/stats` | Task statistics |
| POST | `/reset` | Reset example tasks |

## Security notes

- Authentication credentials are handled by Supabase Auth rather than custom password hashing.
- The backend never stores user passwords.
- Protected routes verify the submitted JWT with Supabase before returning private user information.
- `.env` is ignored by Git.
- Do not use a Supabase service-role key in this assignment's client-facing configuration.
- The access token should be treated as a credential and never pasted into GitHub, screenshots, or the README.

## Stage / commit checklist

The assignment asks for at least six meaningful commits. Suggested history:

```text
Stage 0: setup server and supabase client
Stage 1: signup and login routes working
Stage 2: public route and unverified protected route
Stage 3: profile route token verification
Stage 4: auth middleware and logout endpoint
Stage 5: Swagger UI documentation with bearer auth
Stage 6: publish to GitHub and write README
```

If the work is being submitted as one final archive rather than through the Git history, keep the commit history in the GitHub repository and use the checklist above to demonstrate the stages.

## Assignment completion checklist

- [x] Server starts with Uvicorn.
- [x] `.env` is ignored and `.env.example` documents required variables.
- [x] `POST /auth/signup` uses Supabase Auth.
- [x] `POST /auth/login` uses Supabase Auth and returns access/refresh tokens.
- [x] `GET /public/info` is public.
- [x] `GET /protected/profile` verifies the Bearer JWT with Supabase.
- [x] Authentication logic is reusable through a FastAPI dependency.
- [x] `GET /protected/dashboard` reuses the same dependency.
- [x] `POST /auth/logout` is protected.
- [x] Swagger UI is available at `/docs`.
- [x] Protected endpoints advertise Bearer authentication in OpenAPI.
- [x] Existing PostgreSQL Task CRUD API remains available.
- [ ] GitHub repository published with six meaningful commits.
- [ ] Swagger screenshot added to the repository/README after local testing.

## AI Rematch — optional

For the bonus stage, ask an AI assistant to reproduce this authentication flow from memory. Compare its implementation against this version, especially:

- Bearer prefix extraction
- Missing-header behavior
- Invalid-token handling
- Status-code accuracy
- Environment-variable handling
- Swagger security configuration

Document any security or correctness differences in an `AI vs Me` section after testing both implementations.
