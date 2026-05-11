from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "retail.db"


def format_table(columns: list[str], rows: list[tuple[object, ...]]) -> str:
    values = [[str(value) if value is not None else "" for value in row] for row in rows]
    widths = [
        max(len(column), *(len(row[idx]) for row in values)) if values else len(column)
        for idx, column in enumerate(columns)
    ]

    def line(items: list[str]) -> str:
        return " | ".join(item.ljust(widths[idx]) for idx, item in enumerate(items))

    output = [line(columns), "-+-".join("-" * width for width in widths)]
    output.extend(line(row) for row in values)
    return "\n".join(output)


def main() -> None:
    sql = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else sys.stdin.read().strip()
    if not sql:
        raise SystemExit("Usage: python3 scripts/run_query.py \"SELECT ...\"")
    if not DB_PATH.exists():
        raise SystemExit("Database not found. Run: python3 scripts/init_db.py")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description or []]

    if columns:
        print(format_table(columns, rows))
        print(f"\nReturned {len(rows)} row(s).")
    else:
        print("Query executed.")


if __name__ == "__main__":
    main()
