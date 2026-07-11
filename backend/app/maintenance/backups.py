"""Daily PostgreSQL backup script (M8.4)."""

import os
import subprocess
from datetime import date
from pathlib import Path


def main() -> None:
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise SystemExit("DATABASE_URL not set")

    backup_dir = Path(__file__).resolve().parents[2] / "backups"
    backup_dir.mkdir(exist_ok=True)
    outfile = backup_dir / f"opportunity_radar_{date.today().isoformat()}.sql"

    # pg_dump expects postgresql:// not postgresql+psycopg://
    pg_url = db_url.replace("postgresql+psycopg://", "postgresql://")
    subprocess.run(["pg_dump", pg_url, "-f", str(outfile)], check=True)
    print(f"Backup written to {outfile}")


if __name__ == "__main__":
    main()
