# Nivara Agent Transfer

## Current Status

Foundation implementation is complete and runnable at the application level.
No product feature domains have been implemented yet.

## Last Completed Tasks

- T001 Repository foundation
- T002 Frontend foundation
- T003 Backend foundation
- T004 Database foundation
- T005 Configuration/environment foundation
- T006 API foundation
- T007 Testing foundation

## Current Architecture

Backend:

- `backend/app/main.py` creates the FastAPI app and registers CORS, errors,
  and routers.
- `backend/app/core` owns environment-backed settings and structured request
  validation errors.
- `backend/app/api` owns HTTP routes. Only health is implemented.
- `backend/app/services` owns business services. Health response construction
  is the initial example.
- `backend/app/repositories` and `backend/app/models` are intentionally empty
  boundaries for domain agents.
- `backend/app/db/session.py` owns the async SQLAlchemy engine and session
  dependency. It is compatible with PostgreSQL/PostGIS via `asyncpg`.

Frontend:

- Next.js App Router + TypeScript + Tailwind CSS.
- `frontend/components/ui` is shadcn-compatible shared UI space.
- `frontend/lib/api.ts` owns the API base URL configuration.
- `frontend/app/page.tsx` is only a minimal application shell.

Database:

- `docker-compose.yml` provides local PostgreSQL 16 with PostGIS 3.4.
- No migrations or domain tables exist yet; the next database-owning feature
  should introduce them deliberately.

## Files Created or Modified

- `backend/` FastAPI package, dependency metadata, README, and health tests
- `frontend/` Next.js application, Tailwind config, UI primitive, and shell
- `docker-compose.yml`
- `.env.example`
- `docs/tasks.md`, `docs/api.md`, `docs/architecture.md`, `docs/decisions.md`
- this handoff document

## Verification Performed

- `python3 -m pip install -e '.[test]' --user` from `backend/` — passed
- `pytest -q` from `backend/` — passed, 2 tests
- `uvicorn app.main:app --host 127.0.0.1 --port 8000` — app started successfully
- The environment disallowed a separate `curl` socket request; ASGI smoke
  tests use in-process HTTP transport instead.
- `pnpm install` from `frontend/` — passed
- `pnpm typecheck` from `frontend/` — passed
- `pnpm build` from `frontend/` — passed
- `pnpm start` from `frontend/` — blocked by the sandbox refusing a local
  port bind (`EPERM` on `0.0.0.0:3000`), not by a build or application error.

## Environment Variables

See `.env.example`: `APP_ENV`, `APP_DEBUG`, `CORS_ORIGINS`, `DATABASE_URL`,
optional map/AI/notification credentials, and `NEXT_PUBLIC_API_URL`.

Never commit `.env` or real credentials.

## Known Limitations

- No authentication, migrations, domain models, map provider, or feature APIs.
- The health endpoint reports that the database URL is configured; it does not
  perform a database connectivity probe.
- Local PostGIS requires Docker/Compose to be available.
- This sandbox disallows local TCP port binding for the Next.js server and
  external `curl`; normal local development environments should not have that
  restriction.

## Exact Next Task

T010 — Map integration, after the safety and incident ownership agents have
agreed on the route/indicator contract. The immediate foundation follow-up is
to add database migrations only when the first domain model is ready.
