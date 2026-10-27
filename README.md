# FastAPI Auth API (Docker Compose)

A small authentication API built with FastAPI, async SQLAlchemy and PostgreSQL. It supports sign-up, login with JWT tokens, and a protected `/me` endpoint, with role-based access. The whole stack starts with one Docker Compose command.

## What's inside

- **api**: the FastAPI app, served by uvicorn (Python 3.12).
- **postgres**: PostgreSQL 16 with a named volume (`pgdata`), so your data survives restarts.

## Quick start

Requirements: Docker with Compose.

1. Clone the repo:

```bash
git clone -b docker-compose https://github.com/Phvl-0/FastApi-Supabase-Auth.git
cd FastApi-Supabase-Auth
```

2. Create your own `.env` file with random secrets (it is ignored by Git, so it never gets committed):

```bash
cat > .env << EOF
POSTGRES_PASSWORD=$(openssl rand -hex 16)
SECRET_KEY=$(openssl rand -hex 32)
EOF
chmod 600 .env
```

3. Start everything:

```bash
docker compose up --build
```

4. Open http://localhost:8000/docs to use the interactive Swagger page.

## Using the API

In the Swagger page: register a user, log in to get a JWT, click **Authorize** and paste the token, then call `GET /me`.

## Stopping

```bash
docker compose down        # stops the stack, keeps your data
docker compose down -v     # stops the stack AND deletes the database volume
```

## Security notes

- Secrets come from the environment (`.env`), not from the code. The app refuses to start without `SECRET_KEY`.
- The database is not exposed to the host, and the API is bound to `127.0.0.1` only.
- The sign-up endpoint ignores any `id` or `role` sent by the caller: the server generates the id and every new user gets the role `voter`. This closes a privilege-escalation (mass-assignment) bug found during testing.
- A placeholder secret in the project's first commit has been replaced and must never be used. If you deploy this, generate your own keys.

## Limitations

- This is a development setup: plain HTTP, no HTTPS or reverse proxy.
- Dependency versions are not pinned yet, and some libraries (passlib, python-jose) are aging and may be replaced.
- The container image has not been security-scanned yet.
- The original version of this project used Supabase. This setup uses a local PostgreSQL container instead.
