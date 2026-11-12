"""Data quality tests for the marts layer. The pipeline is not trusted until all of these pass."""
from pathlib import Path
import sqlite3
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "olist"


@pytest.fixture(scope="module")
def con():
    c = sqlite3.connect(ROOT / "data" / "olist.db")
    yield c
    c.close()


def one(con, sql):
    return con.execute(sql).fetchone()[0]


# ---- keys and row counts -------------------------------------------------
def test_order_id_unique_in_fact_orders(con):
    assert one(con, "SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM fact_orders") == 0


def test_fact_orders_has_every_raw_order(con):
    raw = len(pd.read_csv(RAW / "olist_orders_dataset.csv"))
    assert one(con, "SELECT COUNT(*) FROM fact_orders") == raw


def test_fact_order_items_has_every_raw_item(con):
    raw = len(pd.read_csv(RAW / "olist_order_items_dataset.csv"))
    assert one(con, "SELECT COUNT(*) FROM fact_order_items") == raw
    assert one(con, "SELECT COUNT(*) - COUNT(DISTINCT order_id || '-' || order_item_id) FROM fact_order_items") == 0


def test_customer_dimension_is_one_row_per_person(con):
    raw = pd.read_csv(RAW / "olist_customers_dataset.csv").customer_unique_id.nunique()
    assert one(con, "SELECT COUNT(*) FROM dim_customer") == raw
    assert one(con, "SELECT COUNT(*) - COUNT(DISTINCT customer_unique_id) FROM dim_customer") == 0


# ---- reconciliation with the raw files (independent calculation) ---------
def test_revenue_reconciles_with_raw(con):
    o = pd.read_csv(RAW / "olist_orders_dataset.csv", parse_dates=["order_purchase_timestamp"])
    i = pd.read_csv(RAW / "olist_order_items_dataset.csv")
    ok = o[(o.order_status == "delivered") & o.order_delivered_customer_date.notna()
           & o.order_purchase_timestamp.between("2017-01-01", "2018-08-31 23:59:59")]
    expected = i[i.order_id.isin(ok.order_id)].price.sum()
    got = one(con, "SELECT SUM(price) FROM fact_order_items WHERE is_revenue_item = 1")
    assert got == pytest.approx(expected, abs=0.01)


def test_item_totals_match_between_fact_tables(con):
    a = one(con, "SELECT SUM(items_price) FROM fact_orders")
    b = one(con, "SELECT SUM(price) FROM fact_order_items")
    assert a == pytest.approx(b, abs=0.01)   # no row multiplication from joins


def test_late_rate_reconciles_with_raw(con):
    o = pd.read_csv(RAW / "olist_orders_dataset.csv",
                    parse_dates=["order_delivered_customer_date", "order_estimated_delivery_date"])
    d = o.dropna(subset=["order_delivered_customer_date"])
    expected = (d.order_delivered_customer_date > d.order_estimated_delivery_date).mean()
    got = one(con, "SELECT AVG(is_late) FROM fact_orders WHERE is_late IS NOT NULL")
    assert got == pytest.approx(expected, abs=1e-9)


def test_one_review_per_order(con):
    assert one(con, "SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM stg_reviews") == 0


# ---- value sanity ----------------------------------------------------------
def test_no_negative_delivery_days(con):
    assert one(con, "SELECT COUNT(*) FROM fact_orders WHERE delivery_days < 0") == 0


def test_no_negative_prices_or_freight(con):
    assert one(con, "SELECT COUNT(*) FROM fact_order_items WHERE price < 0 OR freight_value < 0") == 0


def test_review_scores_in_range(con):
    assert one(con, "SELECT COUNT(*) FROM fact_orders WHERE review_score NOT BETWEEN 1 AND 5") == 0


def test_distances_are_plausible(con):
    assert one(con, "SELECT COUNT(*) FROM fact_order_items WHERE distance_km < 0 OR distance_km > 4500") == 0


def test_revenue_orders_are_inside_window_and_delivered(con):
    bad = one(con, """SELECT COUNT(*) FROM fact_orders WHERE is_revenue_order = 1
                      AND (in_window = 0 OR is_delivered = 0 OR delivery_days IS NULL)""")
    assert bad == 0


# ---- foreign keys and external data ---------------------------------------
@pytest.mark.parametrize("sql", [
    "SELECT COUNT(*) FROM fact_orders f LEFT JOIN dim_customer d USING (customer_unique_id) WHERE d.customer_unique_id IS NULL",
    "SELECT COUNT(*) FROM fact_order_items f LEFT JOIN dim_seller d USING (seller_id) WHERE d.seller_id IS NULL",
    "SELECT COUNT(*) FROM fact_order_items f LEFT JOIN dim_product d USING (product_id) WHERE d.product_id IS NULL",
    "SELECT COUNT(*) FROM fact_orders f LEFT JOIN dim_date d ON d.date = f.purchase_date WHERE d.date IS NULL",
], ids=["customer", "seller", "product", "date"])
def test_every_fact_row_has_its_dimension_row(con, sql):
    assert one(con, sql) == 0


def test_every_customer_and_seller_state_matches_ibge(con):
    assert one(con, "SELECT COUNT(*) FROM dim_customer WHERE state_population IS NULL") == 0
    assert one(con, "SELECT COUNT(*) FROM dim_seller WHERE state_population IS NULL") == 0


def test_ibge_population_matches_published_total(con):
    assert one(con, "SELECT SUM(population) FROM stg_ibge_states") == 208_494_900


def test_holidays_flagged_in_date_dimension(con):
    # every holiday that falls inside the calendar range must be flagged
    expected = one(con, """SELECT COUNT(*) FROM stg_holidays
                           WHERE date BETWEEN (SELECT MIN(date) FROM dim_date) AND (SELECT MAX(date) FROM dim_date)""")
    assert expected > 0
    assert one(con, "SELECT COUNT(*) FROM dim_date WHERE is_holiday = 1") == expected
