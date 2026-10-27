# Opportunity Radar — current implementation

Updated: 27 October 2026.

## Active scope

News and hackathon discovery, account registration/sign-in/sign-out, private saved articles and hackathons, and personal hackathon application tracking.

Jobs and matching are removed from active navigation, API routes, scraper selection, source configuration, and dashboard. Existing job records and earlier source modules remain preserved. Alerts are not exposed.

## Account and collection implementation

- PostgreSQL accounts, hashed passwords, and revocable sessions (migration 005).
- Seven-day HttpOnly session cookies, Secure in production, SameSite=Lax.
- Database-backed authentication throttling and browser origin checks.
- Account-scoped actions; anonymous legacy records remain unclaimed.
- Save/unsave articles and hackathons; mark applied/undo for hackathons.
- Saved and Applied collections include titles, source/organizer, external links, dates, and action controls.
- Action status, loading, failures, sign-in prompts, and collection empty states.

## Remaining delivery work

- Public HTTPS deployment and evaluator access.
- Fresh news ingestion. Hackathon discovery now uses live sources and filters expired/stale events.
- Demo recording and submission details.
- Email verification/password-reset flows, if required by the intended deployment.
- Automatic news scheduling remains outside the current implementation. Hackathons refresh automatically every six hours while the API runs.

README describes local setup, architecture, configuration, workflows, and validation commands. Tests cover account ownership and session behavior without retaining test accounts in the database.

## Live hackathon discovery

- MLH redirects to its new season page; reads published event JSON with exact start/end timestamps.
- Devpost public open/upcoming listings are paginated; submission-date ranges and single closing dates are supported.
- Provider identities drive updates, including corrected titles, dates, locations, prizes, and status.
- Seed entries are unverified and excluded; distinct editions sharing a URL retain separate records.
- Discovery excludes ended, registration-closed, stale (>48 hours), and source-withdrawn events.
- Source labels, source links, last fetch time, and refresh status are visible.
- Saved/applied history survives expiration, retirement, and source removal.
