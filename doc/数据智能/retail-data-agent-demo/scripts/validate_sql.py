from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "retail.db"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 scripts/validate_sql.py path/to/query.sql")
    if not DB_PATH.exists():
        raise SystemExit("Database not found. Run: python3 scripts/init_db.py")

    sql_path = Path(sys.argv[1])
    sql = sql_path.read_text(encoding="utf-8")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("EXPLAIN QUERY PLAN " + sql)

    print(f"OK: {sql_path} is valid for {DB_PATH}")


if __name__ == "__main__":
    main()
