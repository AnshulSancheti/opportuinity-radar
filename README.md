# Opportunity Radar

A news and hackathon discovery app with accounts, private saved collections, and a hackathon application tracker.

**Production:** https://hackathons.intelligentape.online

The production runtime is Cloudflare Workers + D1 + Queues + Cron Triggers. The Python/PostgreSQL backend remains available locally as the reference implementation and migration source.

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

## Production architecture

- **Frontend:** Next.js 16 static export, React, TypeScript, Tailwind CSS. Cloudflare serves the assets; public feeds and private collections fetch from `/api/v1` on the same HTTPS origin.
- **API:** TypeScript Worker in `cloudflare/`. Prepared D1 queries implement the public feeds, account/session endpoints, personal actions, source status, and operator controls.
- **Database:** Cloudflare D1 (SQLite). Schema migrations live in `cloudflare/migrations/`.
- **Ingestion:** Cron Triggers enqueue hackathon refreshes every six hours and news refreshes hourly. A Queue consumer processes them outside page requests. Database locks prevent concurrent or duplicate operator triggers. Failed hackathon refreshes retry after 15 minutes, up to the queue retry limit.
- **Accounts:** salted scrypt hashes; opaque HttpOnly, Secure, SameSite=Lax cookies. Only session-token hashes are stored. Seven-day sessions are revoked on logout; authentication attempts are throttled by email and IP. Browser mutations reject foreign origins and require JSON where relevant.
- **Migration:** existing Python password hashes remain valid and are upgraded to a lower-memory scrypt configuration on successful sign-in. Account IDs, item IDs, and saved/applied ownership are retained. Browser sessions are intentionally not copied: sign in again on the production domain.
- **Ownership:** personal action reads and writes are scoped by the authenticated account on the API. A user cannot supply an owner ID to access someone else’s items.

Jobs and job matching are retired from the active UI, API, and scraper runner. Their earlier source modules, PostgreSQL tables, and migrations remain locally for preservation. They are not part of the D1 runtime. The old alerts feature is not exposed.

## Cloudflare setup and deployment

```bash
npm ci
npm --prefix frontend ci
npm run build
npx wrangler d1 migrations apply opportunity-radar --remote
npx wrangler secret put ADMIN_PASSWORD
npx wrangler deploy
```

`wrangler.jsonc` defines the account, D1 binding, ingestion queue, custom domain, cron triggers, assets, and observability. For a fresh account, create the D1 database and queue first and replace their resource identifiers. Run migrations before deploying the Worker.

For local Workers development, apply the migrations with `--local`, set a strong `ADMIN_PASSWORD` in an ignored `.dev.vars`, run `npm run build`, then `npm run dev:cloudflare`. Open http://localhost:8787, create an account, and trigger the initial ingestion through Admin.

The one-time migration script `scripts/export-cloudflare.py` runs inside the original backend container. Its SQL output includes private account password hashes and must be redirected into an ignored, restricted file under `.radar/`. Never commit it, never serve it as an asset, and do not repeat an initial import against a populated database. The local PostgreSQL data is preserved.

## Original Python/PostgreSQL setup

Requires Docker with Compose and Node.js 24 / npm.

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

For this original backend, set `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` in `frontend/.env.local` (the launcher writes it automatically). Keep the frontend terminal running. Stop services with `bash start.sh --stop` (or Ctrl+C for a manually launched frontend).

## Original backend configuration

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
npm run typecheck
npm run test:cloudflare
npm run build
python scripts/smoke-cloudflare.py http://localhost:8787
# Original backend regression suite:
docker compose exec -T backend pytest -q
```

The Workers tests cover existing password compatibility, current password hashing, provider/date parsing, safe URLs, RSS/Atom parsing, and stable identities. The HTTP smoke script uses disposable accounts to check registration, login/logout, ownership isolation, save/unsave, applied/undo, revoked sessions, validation, origin protection, and operator rejection. It writes exact account-cleanup SQL into `.radar/`; apply that to the corresponding test database after the run.

The original backend integration tests roll back their transactions without retaining test accounts.

## Feed semantics and limits

Discovery shows only live MLH/Devpost records fetched within the last 48 hours whose end date and any known registration deadline have not passed. Events missing from a complete successful refresh leave discovery. Source failures retain recent prior data and show the last successful fetch time. Manual seed records are retired as `unverified`; saved/applied records remain accessible.

MLH dates are its published ISO timestamps. Devpost submission ranges are calendar dates, normalized to UTC day boundaries for filtering. They are not registration deadlines. Missing metadata is not invented. Distinct annual editions may share a website, so provider identities determine updates. Confirm registration requirements on the linked event website.

News sources include the configured RSS/Atom publishers, Dev.to, and Hacker News. Individual source failures are recorded in Admin; other sources continue refreshing. External providers can change their formats or access policies, so inspect source status when a feed looks stale.

Email verification, password reset, and a demo recording remain future work. Session state and private collections use caching-disabled requests. Passwords and session tokens are never placed in browser localStorage.
