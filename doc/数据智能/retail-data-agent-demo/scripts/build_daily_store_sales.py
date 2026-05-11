from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "retail.db"
SQL_PATH = ROOT / "marts" / "build_daily_store_sales.sql"


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit("Database not found. Run: python3 scripts/init_db.py")

    sql = SQL_PATH.read_text(encoding="utf-8")

    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(sql)
        checks = {
            "row_count": conn.execute("SELECT COUNT(*) FROM daily_store_sales").fetchone()[0],
            "duplicate_keys": conn.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT biz_date, store_id, COUNT(*) AS cnt
                    FROM daily_store_sales
                    GROUP BY biz_date, store_id
                    HAVING cnt > 1
                )
                """
            ).fetchone()[0],
            "null_core_metrics": conn.execute(
                """
                SELECT COUNT(*)
                FROM daily_store_sales
                WHERE gmv IS NULL OR order_count IS NULL OR aov IS NULL OR gross_profit IS NULL
                """
            ).fetchone()[0],
            "negative_amounts": conn.execute(
                """
                SELECT COUNT(*)
                FROM daily_store_sales
                WHERE gmv < 0 OR gross_profit < 0 OR refund_amount < 0
                """
            ).fetchone()[0],
        }
        sample_rows = conn.execute(
            """
            SELECT biz_date, store_name, region, ROUND(gmv, 2) AS gmv, order_count, ROUND(aov, 2) AS aov
            FROM daily_store_sales
            ORDER BY biz_date DESC, gmv DESC
            LIMIT 5
            """
        ).fetchall()
        conn.commit()

    if checks["row_count"] <= 0:
        raise SystemExit("Quality check failed: daily_store_sales has no rows")
    if checks["duplicate_keys"] != 0:
        raise SystemExit("Quality check failed: duplicate biz_date + store_id keys")
    if checks["null_core_metrics"] != 0:
        raise SystemExit("Quality check failed: null core metrics")
    if checks["negative_amounts"] != 0:
        raise SystemExit("Quality check failed: negative amount metrics")

    print("Built mart: daily_store_sales")
    for name, value in checks.items():
        print(f"{name}: {value}")
    print("sample:")
    for row in sample_rows:
        print(row)


if __name__ == "__main__":
    main()
