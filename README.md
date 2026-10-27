# Opportunity Radar

A news and hackathon discovery app with accounts, private saved collections, and a hackathon application tracker.

## Problem and target users

Students and developers follow several news sources and hackathon organizers. Useful articles and events get lost across tabs, and it is difficult to remember which hackathons they have already applied to.

Radar brings these feeds together. Each user can search news and hackathons, save interesting items, and keep a personal record of submitted hackathon applications.

## Main workflows

1. Browse and filter news or hackathons without an account.
2. Create an email/password account or sign in.
3. Save articles and hackathons, then open them from a private collection.
4. Apply through the organizer’s website and select **Mark applied** in Radar. View or undo this status in **Applied**. Radar does not submit applications.
5. Hackathons refresh automatically every six hours while the API runs. Authorized operators can also trigger news/hackathon scrapes and inspect run history.

Save and applied statuses are independent and can both be removed. Old anonymous saved records are not assigned to newly registered users.

## Stack and architecture

- **Frontend:** Next.js 14, React, TypeScript, Tailwind CSS. Public feeds render on the server; account and collection views fetch with session credentials in the browser.
- **API:** Python/FastAPI, Pydantic validation, SQLAlchemy.
- **Persistence:** PostgreSQL 16; Alembic migrations run at backend startup.
- **Ingestion:** configurable news feeds plus live MLH and Devpost hackathon listings, normalization, stable provider identities, and source/run logs. Redirects are followed; MLH structured JSON and Devpost paginated JSON are parsed. A source format failure is logged rather than replaced with synthetic events.
- **Accounts:** salted scrypt password hashes; random opaque session cookies (HttpOnly, SameSite=Lax), stored as SHA-256 hashes in PostgreSQL. Sessions expire after seven days and are revoked on sign-out. Registration/login are throttled by email and IP over a 15-minute window. Browser mutations validate origins and require JSON bodies.
- **Ownership:** personal action reads and writes are scoped by the authenticated account on the API. A user cannot supply an owner ID to access someone else’s items.

Jobs and job matching are retired from the active UI, API, and scraper runner. Existing job tables, migrations, and source modules remain for compatibility and preservation of earlier work. The old alerts feature is not exposed in this version.

## Local setup

Requires Docker with Compose and Node.js 20+ / npm.

```bash
cp .env.example .env  # only if .env does not exist
bash start.sh
```

The launcher builds the backend, starts PostgreSQL, runs migrations, and starts the frontend. Open **http://localhost:3000**. API documentation: **http://localhost:8000/docs**.

Alternatively:

```bash
docker compose up -d --build postgres backend
cd frontend
npm install
npm run dev
```

Keep the frontend terminal running. Stop services with `bash start.sh --stop` (or Ctrl+C for a manually launched frontend).

## Configuration

Use `.env.example` as a reference; never commit real credentials.

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL URL. Compose supplies the internal container URL. |
| `NEXT_PUBLIC_API_URL` | Browser-accessible API base URL including `/api/v1`; local default `http://localhost:8000/api/v1`. |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins, with scheme and port, without trailing slash. |
| `API_ENV` | Use `production` under HTTPS to enable Secure session cookies; local HTTP uses development. |
| `HACKATHON_AUTO_REFRESH` | Enables automatic hackathon ingestion while the API runs; default `true`. |
| `HACKATHON_REFRESH_HOURS` | Refresh interval; default `6` hours. Failed refreshes are retried after 15 minutes. |
| `ADMIN_PASSWORD` | Separate operator passphrase. Default/example passphrases are rejected. Admin actions also require a signed-in account. |
| `SCRAPER_DEFAULT_DELAY_MS`, `SCRAPER_DEFAULT_TIMEOUT_SECONDS`, `SCRAPER_DEFAULT_MAX_RETRIES` | Ingestion limits. |

To use Admin, configure a strong `ADMIN_PASSWORD` in `.env`, recreate the backend (`docker compose up -d --force-recreate backend`), sign in, and enter the passphrase at `/admin`. The passphrase grants operator access; ordinary accounts do not grant it automatically.

## Routes

| Route | Purpose |
|---|---|
| `/` | Public dashboard |
| `/news` | Search and save articles |
| `/hackathons` | Search, save, and mark hackathons applied |
| `/login` | Sign in or create an account |
| `/saved` | Private saved articles and hackathons |
| `/applied` | Private hackathon application tracker |
| `/admin` | Operator ingestion controls |

## Validation

```bash
docker compose exec -T backend pytest -q
cd frontend
npx tsc --noEmit
npm run build
```

Account integration tests roll back their transactions. They cover registration, login/logout, expiration/revocation, duplicate registration, user isolation, save/unsave, applied/undo, invalid actions, anonymous denial, origin protection, throttling, and removal of job endpoints.

## Deployment and limits

The current verified deployment is local. No public deployment URL or demo recording is supplied yet.

For hosting, provide PostgreSQL, run `alembic upgrade head`, serve the API and frontend with HTTPS, configure the public API URL and exact allowed frontend origin, set `API_ENV=production`, and use a strong operator passphrase. Host frontend and API on the same site (for example `radar.example.com` and `api.example.com`) for SameSite cookies. Do not expose PostgreSQL publicly. The included Compose configuration is for local development.

Hackathon refresh runs in the API lifespan, checks freshness each minute, and starts ingestion when due. It does not require the legacy worker. On startup it refreshes missing/stale sources. News scheduling remains manual. For a scaled deployment, move periodic ingestion to a single dedicated scheduler.

Discovery shows only live MLH/Devpost records fetched within the last 48 hours whose end date and any known registration deadline have not passed. Events missing from a complete successful refresh leave discovery. Source failures retain recent prior data and show the last successful fetch time. Manual seed records are retired as `unverified`; saved/applied records remain accessible.

MLH event dates are the published ISO timestamps. Devpost submission ranges are calendar dates (normalized to UTC day boundaries for filtering), not claimed registration deadlines. Missing dates and metadata are not invented. Distinct annual editions may share an organizer website, so provider identities determine updates. Confirm registration requirements on the linked event website. Email verification and password-reset delivery are not implemented.

Sign-in state and private collections are fetched from the API with caching disabled. Passwords and session tokens are never placed in browser localStorage.
