# Opportunity Radar — Implementation Progress

> Living tracker aligned with the corrected implementation plan. 
**Started:** 2026-07-05  
**Last updated:** 2026-07-05 
**Current milestone:** M8 — Complete (Valorant UI + expanded scrapers)

---

## Milestone overview

| Milestone | Name | Status | Notes |
|-----------|------|--------|-------|
| M0 | Project Scaffold | ✅ Done | Health, Docker, Postgres |
| M1 | Data Layer | ✅ Done | Models, Alembic, CRUD APIs |
| M2 | Scraper Foundation | ✅ Done | BaseScraper, cleaner, CLI runner |
| M3 | News Pipeline | ✅ Done | RSS + HN, categorizer, `/news` |
| M4 | Jobs Pipeline | ✅ Done | Greenhouse + Lever, skills, `/jobs` |
| M5 | Hackathons Pipeline | ✅ Done | static_list + MLH attempt, `/hackathons` |
| M6 | Product Layer | ✅ Done | Actions, dashboard, alerts API |
| M7 | Quality & Maintenance | ✅ Done | Cleanup, unit tests (5 passing) |
| M8 | Deployment & Operations | ✅ Done | Docker Compose, admin auth, backup script |

---

## MVP tracker

| MVP | Scope | Status |
|-----|-------|--------|
| MVP 1 | News pipeline + `/news` | ✅ Done — 60 articles |
| MVP 2 | Jobs pipeline + `/jobs` | ✅ Done — 590 jobs |
| MVP 3 | Hackathons + `/hackathons` | ✅ Done — 3 events (static_list) |
| MVP 4 | Search, alerts, Docker prod | ✅ Done — ILIKE search, Telegram ready |

---

## Verified data (2026-07-05)

| Metric | Count |
|--------|------:|
| Articles | 60 |
| Jobs | 590 |
| Hackathons | 3 |
| Scrape runs logged | Yes |

---

## Pre-flight checklist

- [x] Synthetic HN URLs for text posts
- [x] Greenhouse list-only ingest (detail fetch removed — too slow)
- [x] Batch-only alert dispatch (`app.alerts.dispatch`)
- [x] `sources.yaml` config file
- [x] Orphaned `scrape_runs` cleanup (>2h running → failed)
- [x] Worker shares Python package + DB layer with backend

---

## How to run

```bash
# Start backend + database
docker compose up -d postgres backend

# Run scrapers
docker compose exec backend python -m app.scrapers.runner --module news
docker compose exec backend python -m app.scrapers.runner --module jobs
docker compose exec backend python -m app.scrapers.runner --module hackathons

# Frontend (local dev)
cd frontend && npm install && npm run dev

# Tests
cd backend && python -m pytest tests/ -v

# Cleanup
docker compose exec backend python -m app.maintenance.cleanup
```

---

## Session log

| Date | Stage | Summary |
|------|-------|---------|
| 2026-07-05 | M0.1–M0.3 | Repo, FastAPI health, Docker Compose + Postgres |
| 2026-07-05 | M1–M2 | Models, Alembic, BaseScraper, cleaner, runner |
| 2026-07-05 | M3 | RSS + HN scrapers, news API, `/news` page |
| 2026-07-05 | M4 | Greenhouse + Lever jobs, skills, `/jobs` page |
| 2026-07-05 | M5 | Hackathons (static_list), `/hackathons` page |
| 2026-07-05 | M6–M8 | Dashboard, actions, alerts, admin, tests, cleanup |

---

## Known limitations

- MLH scraper returns 0 (JS-heavy page) — `static_list` used as fallback
- Netflix Lever board returned 0 jobs — Plaid configured as replacement
- Telegram alerts require `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`
- `pg_trgm` fuzzy search deferred — ILIKE filters work for MVP
