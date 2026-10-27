# Cloudflare deployment verification

Verified on 27 October 2026.

- Production: https://hackathons.intelligentape.online
- Worker: `opportunity-radar`
- Deployment version: `1421b0f1-81df-4142-bbc2-a71b5afb470d`
- D1: `opportunity-radar`
- Ingestion queue: `opportunity-radar-ingestion`
- Hackathon cron: `0 */6 * * *` (UTC)
- News cron: `30 * * * *` (UTC)
- Public workers.dev and preview URLs remain disabled.

## Data preservation

The initial D1 import retained one account, two personal/legacy action records, 244 articles, 254 hackathon records, and 20 relevant scrape-run records. Original account IDs, item IDs, password hashes, and action ownership were retained. Local PostgreSQL was not deleted or replaced. Browser sessions were not transferred; use the existing password to sign in on the production hostname.

The original 17 seed hackathons remain unverified and excluded from discovery. Both live source refreshes subsequently completed on Cloudflare: 63 MLH events and 174 Devpost events. All 12 news sources refreshed successfully, and the scheduled hourly news job was observed running after deployment. At verification the API reported 499 articles, 237 discoverable hackathons, no failed sources, and no active scrapes.

Three disposable production verification accounts were deleted by exact IDs and test-email predicates after testing. Reconciliation confirmed one retained account, two original action records, and zero verification accounts.

## Checks performed

- Worker TypeScript check and 11 dedicated tests passed.
- Next.js 16 / React 19 production static export and ESLint checks passed.
- Worker and frontend production dependency audits reported zero known vulnerabilities.
- Public HTTPS pages, API health, source status, and feed counts were checked.
- Static JavaScript/CSS assets were compared with the final local build; exported route-navigation payloads were checked.
- Live API tests covered registration, duplicate registration, login/logout, secure-cookie flags, revoked sessions, account isolation, saved articles/hackathons, applied/undo, validation, origin rejection, and rejection of ordinary-user operator requests.
- Existing Python scrypt hashes were verified in the actual deployed Workers runtime using a disposable compatibility fixture.
- Cron schedules, queue consumer/producer, and disabled workers.dev routes were read back from Cloudflare.

No interactive browser session was available in this environment. UI validation covers build/lint, deployed pages/assets, and the APIs supporting its workflows; it does not claim a manual visual/browser walkthrough.

Private SQL exports, migration logs, disposable credentials, local database files, and operator secrets are excluded from Git. Deployment code and instructions are maintained in the repository.
