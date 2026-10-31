# FastAPI Auth API (Docker Compose)

A small authentication API built with FastAPI, async SQLAlchemy and PostgreSQL. It supports sign-up, login with JWT tokens, and a protected `/me` endpoint. Each user has a role (new users get `voter`), but no endpoint enforces roles yet. The whole stack starts with one Docker Compose command.

## What's inside

- **api**: the FastAPI app, served by uvicorn (Python 3.12).
- **postgres**: PostgreSQL 16 with a named volume (`pgdata`), so your data survives restarts.
- **nginx**: a reverse proxy in front of the API. It serves HTTPS and is the only service reachable from your machine.

## Quick start

Requirements: Docker with Compose, and a Unix-style shell with `openssl` (Linux, macOS or WSL).

1. Clone the repo:

```bash
git clone https://github.com/Phvl-0/FastApi-Auth-Compose.git
cd FastApi-Auth-Compose
```

2. Create your own `.env` file with random secrets (it is ignored by Git, so it never gets committed):

```bash
cat > .env << EOF
POSTGRES_PASSWORD=$(openssl rand -hex 16)
SECRET_KEY=$(openssl rand -hex 32)
EOF
chmod 600 .env
```

Create `.env` only once. The database saves its password the first time it starts, so a different `.env` created later will not match it. If you need to start over, run `docker compose down -v` first (this deletes the data).

3. Create a self-signed certificate for HTTPS (the `certs/` folder is ignored by Git, so the private key never gets committed):

```bash
mkdir -p certs
openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout certs/localhost.key -out certs/localhost.crt \
  -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
chmod 600 certs/localhost.key
```

4. Start everything:

```bash
docker compose up --build
```

Press `Ctrl+C` to stop it, or add `-d` to run it in the background.

5. Open https://localhost:8443/docs to use the interactive Swagger page. Your browser will warn about the self-signed certificate, which is expected for a local setup. Plain HTTP on port 8088 redirects to HTTPS.

## Using the API

In the Swagger page: register a user, log in to get a JWT, click **Authorize** and paste the token, then call `GET /me`.

## Stopping

```bash
docker compose down        # stops the stack, keeps your data
docker compose down -v     # stops the stack AND deletes the database volume
```

## Security notes

- Secrets come from the environment (`.env`), not from the code. The app refuses to start without `SECRET_KEY`.
- The database and the API are not exposed to the host. Only the nginx reverse proxy is, bound to `127.0.0.1` (ports 8088 and 8443). It serves HTTPS (TLS 1.2 and 1.3), hides its version and adds `nosniff` and frame-denial headers.
- The sign-up endpoint ignores any `id` or `role` sent by the caller: the server generates the id and every new user gets the role `voter`. This closes a privilege-escalation (mass-assignment) bug found during testing.
- A placeholder secret in the project's first commit has been replaced and must never be used. If you deploy this, generate your own keys.

## Limitations

- This is a development setup: the HTTPS certificate is self-signed, so browsers warn about it. A real deployment needs a trusted certificate (for example Let's Encrypt) and a domain.
- Dependency versions are pinned in `requirements.txt`. `passlib` is aging and may be replaced. The JWT library was changed from `python-jose` (open critical vulnerability CVE-2026-85394, no fixed release) to `PyJWT`.
- The image is scanned with Trivy on every push by a GitHub Actions workflow (`.github/workflows/trivy.yml`): the actions are pinned to commit SHAs, the job has read-only permissions, and it fails on HIGH or CRITICAL findings that have a fix available. A manual scan on 2026-10-30 found 2 Python findings before the JWT library swap (`python-jose` and its dependency `ecdsa`) and 0 after. The Debian base image had 44 HIGH findings with no fix available yet; the workflow ignores unfixed findings, so those are not flagged. A clean scan means no known vulnerabilities in the database at scan time, not that the app is secure.
- The original version of this project used Supabase. This setup uses a local PostgreSQL container instead.
