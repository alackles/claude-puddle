# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

Claude Puddle is a teaching assistant chatbot for CMSC 150 (Intro CS) at Lawrence University. Students ask questions about Java programming; Claude guides them (without giving answers directly) using the *Think Java, 2nd Edition* textbook loaded on-demand via tool use. Conversations persist per student and can be shared with instructors for review.

## Running Locally

```bash
# Required environment variables
export ANTHROPIC_API_KEY="sk-..."
export SESSION_SECRET="some-secret-key"
export DB_PATH="./db.sqlite3"
export CONTEXT_DIR="./context"

uvicorn app.main:app --reload
# Runs at http://localhost:8000
```

Dependencies are managed with `uv`:
```bash
uv pip install --system -r pyproject.toml
```

## Managing Invite Codes

Registration is gated by instructor-controlled invite codes:
```bash
python scripts/seed_invite_code.py add <code> <label>
python scripts/seed_invite_code.py deactivate <code>
python scripts/seed_invite_code.py list
```

## Architecture

**Backend:** FastAPI (async) + SQLite via aiosqlite. All routes are in `app/*/router.py`. DB queries are centralized in [app/db/queries.py](app/db/queries.py); schema is in [app/db/schema.sql](app/db/schema.sql).

**Frontend:** Vanilla JS SPA in `static/`. No build step — files are served directly. Session state is tracked client-side via HTTP-only cookies.

**AI integration:** [app/chat/anthropic_client.py](app/chat/anthropic_client.py) runs a tool-use loop — Claude can call `load_chapter` to fetch a chapter PDF from disk, which is sent back as an Anthropic document block. This repeats until Claude stops requesting tools. Responses stream to the frontend via SSE.

**Config:** All settings come from environment variables via [app/config.py](app/config.py). Key settings: `anthropic_api_key`, `session_secret`, `db_path`, `context_dir`, `model` (defaults to `claude-sonnet-4-6`).

## Key Architectural Patterns

- **CSRF protection:** Mutation endpoints (POST/PUT/PATCH/DELETE) enforce `Content-Type: application/json`. No CSRF token required — the content-type check is the protection.
- **Auth:** Session tokens are signed cookies via `itsdangerous`. `get_current_user` and `require_instructor` in [app/auth/dependencies.py](app/auth/dependencies.py) are FastAPI dependency injections used on protected routes.
- **History truncation:** Conversations are capped at 40 messages in [app/chat/context.py](app/chat/context.py) — oldest messages are dropped to manage token budget.
- **Role-based access:** `is_instructor` flag on the user row. Instructors see all shared conversations; students see only their own.
- **Textbook chapters:** PDFs live in `context/chapters/`. The `load_chapter` tool in [app/chat/tools.py](app/chat/tools.py) resolves chapter numbers to file paths and encodes them for the Anthropic API.

## Deployment

Deployed on Fly.io (`fly.toml`). Persistent data (DB + context) is on a volume mounted at `/data`. The `CONTEXT_DIR=/data/context` environment variable points Claude at the chapter PDFs — these must be copied to the volume separately from the Docker image.

## No Tests

There is no test suite. There is no testing framework configured.
