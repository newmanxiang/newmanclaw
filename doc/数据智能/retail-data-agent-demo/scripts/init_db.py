from __future__ import annotations

import csv
import sqlite3
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SEED_DIR = DATA_DIR / "seed"
DB_PATH = DATA_DIR / "retail.db"

MAX_DATE = date(2026, 5, 10)
START_DATE = MAX_DATE - timedelta(days=29)


STORES = [
    {"store_id": "S001", "store_name": "上海南京东路店", "city": "上海", "region": "华东", "store_type": "旗舰店", "open_date": "2022-03-18"},
    {"store_id": "S002", "store_name": "杭州西湖店", "city": "杭州", "region": "华东", "store_type": "标准店", "open_date": "2021-09-10"},
    {"store_id": "S003", "store_name": "北京朝阳店", "city": "北京", "region": "华北", "store_type": "旗舰店", "open_date": "2020-06-01"},
    {"store_id": "S004", "store_name": "天津和平店", "city": "天津", "region": "华北", "store_type": "标准店", "open_date": "2023-01-08"},
    {"store_id": "S005", "store_name": "广州天河店", "city": "广州", "region": "华南", "store_type": "旗舰店", "open_date": "2021-04-22"},
    {"store_id": "S006", "store_name": "深圳南山店", "city": "深圳", "region": "华南", "store_type": "标准店", "open_date": "2022-11-05"},
    {"store_id": "S007", "store_name": "成都春熙路店", "city": "成都", "region": "西南", "store_type": "旗舰店", "open_date": "2020-10-16"},
    {"store_id": "S008", "store_name": "重庆解放碑店", "city": "重庆", "region": "西南", "store_type": "标准店", "open_date": "2023-07-20"},
]


PRODUCTS = [
    {"sku_id": "P001", "sku_name": "精品拿铁", "category_l1": "饮品", "category_l2": "咖啡", "list_price": 28.0, "cost_price": 10.5},
    {"sku_id": "P002", "sku_name": "冷萃咖啡", "category_l1": "饮品", "category_l2": "咖啡", "list_price": 32.0, "cost_price": 12.0},
    {"sku_id": "P003", "sku_name": "鲜榨橙汁", "category_l1": "饮品", "category_l2": "果汁", "list_price": 26.0, "cost_price": 11.0},
    {"sku_id": "P004", "sku_name": "气泡水", "category_l1": "饮品", "category_l2": "汽水", "list_price": 18.0, "cost_price": 6.0},
    {"sku_id": "P005", "sku_name": "牛角包", "category_l1": "烘焙", "category_l2": "面包", "list_price": 16.0, "cost_price": 5.0},
    {"sku_id": "P006", "sku_name": "蓝莓贝果", "category_l1": "烘焙", "category_l2": "面包", "list_price": 20.0, "cost_price": 7.0},
    {"sku_id": "P007", "sku_name": "芝士蛋糕", "category_l1": "烘焙", "category_l2": "蛋糕", "list_price": 36.0, "cost_price": 15.0},
    {"sku_id": "P008", "sku_name": "提拉米苏", "category_l1": "烘焙", "category_l2": "蛋糕", "list_price": 38.0, "cost_price": 16.0},
    {"sku_id": "P009", "sku_name": "坚果礼盒", "category_l1": "零食", "category_l2": "坚果", "list_price": 88.0, "cost_price": 48.0},
    {"sku_id": "P010", "sku_name": "混合果干", "category_l1": "零食", "category_l2": "果干", "list_price": 58.0, "cost_price": 30.0},
    {"sku_id": "P011", "sku_name": "黑巧克力", "category_l1": "零食", "category_l2": "巧克力", "list_price": 42.0, "cost_price": 22.0},
    {"sku_id": "P012", "sku_name": "曲奇饼干", "category_l1": "零食", "category_l2": "饼干", "list_price": 35.0, "cost_price": 14.0},
    {"sku_id": "P013", "sku_name": "洗发水", "category_l1": "日化", "category_l2": "洗护", "list_price": 69.0, "cost_price": 36.0},
    {"sku_id": "P014", "sku_name": "沐浴露", "category_l1": "日化", "category_l2": "洗护", "list_price": 59.0, "cost_price": 31.0},
    {"sku_id": "P015", "sku_name": "纸巾组合", "category_l1": "日化", "category_l2": "纸品", "list_price": 49.0, "cost_price": 28.0},
    {"sku_id": "P016", "sku_name": "洗衣凝珠", "category_l1": "日化", "category_l2": "清洁", "list_price": 79.0, "cost_price": 42.0},
    {"sku_id": "P017", "sku_name": "保温杯", "category_l1": "家居", "category_l2": "杯具", "list_price": 99.0, "cost_price": 52.0},
    {"sku_id": "P018", "sku_name": "香薰蜡烛", "category_l1": "家居", "category_l2": "香氛", "list_price": 76.0, "cost_price": 35.0},
    {"sku_id": "P019", "sku_name": "靠垫", "category_l1": "家居", "category_l2": "软装", "list_price": 89.0, "cost_price": 46.0},
    {"sku_id": "P020", "sku_name": "收纳盒", "category_l1": "家居", "category_l2": "收纳", "list_price": 45.0, "cost_price": 20.0},
]


MEMBER_LEVELS = ["普通", "银卡", "金卡", "黑金"]
CHANNELS = ["门店", "App", "小程序", "外卖平台"]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def generate_members() -> list[dict[str, object]]:
    cities = ["上海", "杭州", "北京", "天津", "广州", "深圳", "成都", "重庆"]
    rows: list[dict[str, object]] = []
    for idx in range(1, 33):
        rows.append(
            {
                "member_id": f"M{idx:03d}",
                "join_date": (date(2024, 1, 1) + timedelta(days=idx * 17)).isoformat(),
                "member_level": MEMBER_LEVELS[idx % len(MEMBER_LEVELS)],
                "city": cities[idx % len(cities)],
            }
        )
    return rows


def generate_orders() -> list[dict[str, object]]:
    product_by_id = {row["sku_id"]: row for row in PRODUCTS}
    rows: list[dict[str, object]] = []
    order_seq = 1

    for day_offset in range(30):
        biz_date = START_DATE + timedelta(days=day_offset)
        in_previous_7 = MAX_DATE - timedelta(days=13) <= biz_date <= MAX_DATE - timedelta(days=7)
        in_current_7 = MAX_DATE - timedelta(days=6) <= biz_date <= MAX_DATE

        for store_idx, store in enumerate(STORES):
            is_east = store["region"] == "华东"
            base_lines = 3 + ((day_offset + store_idx) % 2)
            if is_east and in_previous_7:
                base_lines = 9
            elif is_east and in_current_7:
                base_lines = 4

            for line_idx in range(base_lines):
                if is_east and in_previous_7 and line_idx < 5:
                    sku_id = ["P001", "P002", "P003", "P007", "P009"][line_idx % 5]
                    quantity = 3 if line_idx < 3 else 2
                    channel = ["App", "小程序", "App", "门店", "App"][line_idx % 5]
                elif is_east and in_current_7 and line_idx < 3:
                    sku_id = ["P005", "P012", "P015"][line_idx % 3]
                    quantity = 1
                    channel = ["门店", "门店", "小程序"][line_idx % 3]
                else:
                    sku_id = PRODUCTS[(day_offset + store_idx * 3 + line_idx) % len(PRODUCTS)]["sku_id"]
                    quantity = 1 + ((day_offset + line_idx) % 3 == 0)
                    channel = CHANNELS[(day_offset + store_idx + line_idx) % len(CHANNELS)]

                product = product_by_id[sku_id]
                gross_amount = float(product["list_price"]) * int(quantity)
                discount = 0.92 if channel in {"App", "小程序"} else 1.0
                pay_amount = round(gross_amount * discount, 2)
                refund_amount = 0.0
                if is_east and in_current_7 and sku_id in {"P005", "P012"}:
                    refund_amount = round(pay_amount * 0.12, 2)
                elif (day_offset + store_idx + line_idx) % 37 == 0:
                    refund_amount = round(pay_amount * 0.08, 2)

                rows.append(
                    {
                        "order_id": f"O{order_seq:05d}",
                        "order_date": biz_date.isoformat(),
                        "store_id": store["store_id"],
                        "member_id": f"M{((order_seq - 1) % 32) + 1:03d}",
                        "sku_id": sku_id,
                        "quantity": quantity,
                        "pay_amount": pay_amount,
                        "refund_amount": refund_amount,
                        "channel": channel,
                    }
                )
                order_seq += 1

    return rows


def generate_inventory() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    snapshot_dates = [MAX_DATE - timedelta(days=7), MAX_DATE]
    for snapshot_date in snapshot_dates:
        for store_idx, store in enumerate(STORES):
            for product_idx, product in enumerate(PRODUCTS[:12]):
                on_hand_qty = 80 + ((store_idx * 11 + product_idx * 7) % 45)
                if store["region"] == "华东" and product["category_l1"] == "饮品" and snapshot_date == MAX_DATE:
                    on_hand_qty = 18 + product_idx
                rows.append(
                    {
                        "snapshot_date": snapshot_date.isoformat(),
                        "store_id": store["store_id"],
                        "sku_id": product["sku_id"],
                        "on_hand_qty": on_hand_qty,
                        "available_qty": max(on_hand_qty - 3, 0),
                    }
                )
    return rows


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS stores;
        DROP TABLE IF EXISTS members;
        DROP TABLE IF EXISTS inventory_snapshot;

        CREATE TABLE orders (
            order_id TEXT NOT NULL,
            order_date TEXT NOT NULL,
            store_id TEXT NOT NULL,
            member_id TEXT NOT NULL,
            sku_id TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            pay_amount REAL NOT NULL,
            refund_amount REAL NOT NULL,
            channel TEXT NOT NULL,
            PRIMARY KEY (order_id, sku_id)
        );

        CREATE TABLE products (
            sku_id TEXT PRIMARY KEY,
            sku_name TEXT NOT NULL,
            category_l1 TEXT NOT NULL,
            category_l2 TEXT NOT NULL,
            list_price REAL NOT NULL,
            cost_price REAL NOT NULL
        );

        CREATE TABLE stores (
            store_id TEXT PRIMARY KEY,
            store_name TEXT NOT NULL,
            city TEXT NOT NULL,
            region TEXT NOT NULL,
            store_type TEXT NOT NULL,
            open_date TEXT NOT NULL
        );

        CREATE TABLE members (
            member_id TEXT PRIMARY KEY,
            join_date TEXT NOT NULL,
            member_level TEXT NOT NULL,
            city TEXT NOT NULL
        );

        CREATE TABLE inventory_snapshot (
            snapshot_date TEXT NOT NULL,
            store_id TEXT NOT NULL,
            sku_id TEXT NOT NULL,
            on_hand_qty INTEGER NOT NULL,
            available_qty INTEGER NOT NULL,
            PRIMARY KEY (snapshot_date, store_id, sku_id)
        );
        """
    )


def load_csv(conn: sqlite3.Connection, table: str, path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    columns = reader.fieldnames or []
    placeholders = ", ".join(["?"] * len(columns))
    column_sql = ", ".join(columns)
    values = [[row[column] for column in columns] for row in rows]
    conn.executemany(f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})", values)
    return len(rows)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SEED_DIR.mkdir(parents=True, exist_ok=True)

    seed_files = {
        "stores": STORES,
        "products": PRODUCTS,
        "members": generate_members(),
        "orders": generate_orders(),
        "inventory_snapshot": generate_inventory(),
    }

    for table, rows in seed_files.items():
        write_csv(SEED_DIR / f"{table}.csv", rows)

    if DB_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as conn:
        create_schema(conn)
        counts = {table: load_csv(conn, table, SEED_DIR / f"{table}.csv") for table in seed_files}
        conn.commit()

    print(f"Created SQLite database: {DB_PATH}")
    for table, count in counts.items():
        print(f"Loaded {table}: {count} rows")


if __name__ == "__main__":
    main()
