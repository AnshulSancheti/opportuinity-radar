#!/bin/sh
# Cron schedule for worker container (M8.2)
# */30 * * * * python -m app.scrapers.runner --module news
# 0 */6 * * * python -m app.scrapers.runner --module jobs
# 0 */12 * * * python -m app.scrapers.runner --module hackathons
# 30 2 * * * python -m app.maintenance.cleanup
# */15 * * * * python -m app.alerts.dispatch

echo "Opportunity Radar worker ready. Run scrapers manually:"
echo "  python -m app.scrapers.runner --module news"
exec tail -f /dev/null
