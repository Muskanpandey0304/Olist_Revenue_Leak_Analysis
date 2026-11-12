"""Staging -> marts (star schema). Executes sql/10_build_marts.sql on data/olist.db."""
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]

with sqlite3.connect(ROOT / "data" / "olist.db") as con:
    con.executescript((ROOT / "sql" / "10_build_marts.sql").read_text(encoding="utf-8"))
    for t in ["dim_date", "dim_customer", "dim_seller", "dim_product", "fact_order_items", "fact_orders"]:
        print(f"{t}: {con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:,} rows")
