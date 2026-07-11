# Opportunity Radar

Self-hosted personal intelligence dashboard for jobs, tech news, hackathons, and alerts.

## Quick start (Linux/macOS)

```bash
chmod +x start.sh
./start.sh
```

One command starts **Postgres + backend in Docker**, installs frontend deps on first run (needed when moving from Windows), and launches **Next.js dev** on http://localhost:3000.

```bash
./start.sh --stop    # Shut down Docker + frontend
./start.sh --help    # Options
```

**Windows:** use `.\start.ps1` (same flow, opens frontend in a new terminal).

**Manual** (if you prefer):

```bash
cp .env.example .env
docker compose up -d postgres backend
cd frontend && npm install && npm run dev
```

Open http://localhost:3000 — API at http://localhost:8000/docs

### Scraper controls

Use the **Admin** page at http://localhost:3000/admin (passphrase from `ADMIN_PASSWORD` in `.env`). Run news/jobs/hackathon scrapes and view run history from the UI — no CLI required.

## Stack

| Layer | Tech |
|-------|------|
| Backend | Python, FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL 16 |
| Scrapers | httpx, feedparser, BeautifulSoup |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Scheduler | Cron + CLI in worker container |

## Project structure

```text
opportunity-radar/
├── start.sh           # Primary entrypoint (Linux/macOS)
├── start.ps1          # Windows entrypoint
├── docker-compose.yml
├── backend/           # API, scrapers, services
├── frontend/          # Next.js dashboard
├── PROGRESS.md        # Implementation tracker
└── .env.example
```

## Pages

| Route | Description |
|-------|-------------|
| `/` | Dashboard with stats and scrape status |
| `/news` | Tech news feed |
| `/jobs` | Job listings with filters |
| `/hackathons` | Upcoming hackathons |
| `/saved` | Saved items |
| `/alerts` | Alert rules |
| `/admin` | Scraper controls and run logs |

## Scraping principles

- Prefer official APIs and RSS over HTML scraping
- Rate limit every request from day one
- Never scrape LinkedIn, Indeed, Naukri, or X
- Configure sources in `backend/sources.yaml`

## Progress

See [PROGRESS.md](./PROGRESS.md) for milestone status and verification results.
