-- Q1. Are we growing, and where does revenue come from?  (definitions: reports/metrics_definitions.md)

-- 1a. Headline KPIs for the analysis window (2017-01 to 2018-08, delivered orders)
SELECT ROUND(SUM(i.price), 0)                              AS revenue_brl,
       COUNT(DISTINCT i.order_id)                          AS orders,
       COUNT(DISTINCT i.customer_unique_id)                AS customers,
       ROUND(SUM(i.price) / COUNT(DISTINCT i.order_id), 2) AS avg_order_value,
       ROUND(SUM(i.freight_value), 0)                      AS freight_brl
FROM fact_order_items i WHERE i.is_revenue_item = 1;

-- 1b. Repeat rate: customers with 2+ delivered orders in the window
WITH per_cust AS (
    SELECT customer_unique_id, COUNT(*) AS orders
    FROM fact_orders WHERE is_revenue_order = 1 GROUP BY customer_unique_id)
SELECT COUNT(*) AS customers,
       SUM(orders >= 2) AS repeat_customers,
       ROUND(100.0 * SUM(orders >= 2) / COUNT(*), 2) AS repeat_rate_pct,
       ROUND(100.0 * SUM(CASE WHEN orders >= 2 THEN orders ELSE 0 END) / SUM(orders), 2) AS pct_orders_from_repeaters
FROM per_cust;
