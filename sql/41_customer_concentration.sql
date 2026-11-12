-- Q3. How concentrated is revenue among customers? (Pareto by customer)
WITH cust AS (
    SELECT customer_unique_id, SUM(price) AS spend
    FROM fact_order_items WHERE is_revenue_item = 1 GROUP BY customer_unique_id),
r AS (SELECT spend, NTILE(10) OVER (ORDER BY spend DESC) AS decile FROM cust)
SELECT decile, COUNT(*) AS customers, ROUND(SUM(spend), 0) AS revenue,
       ROUND(100.0 * SUM(spend) / SUM(SUM(spend)) OVER (), 1) AS share_pct,
       ROUND(AVG(spend), 0) AS avg_spend
FROM r GROUP BY decile ORDER BY decile;

-- Value of repeat vs one-time customers
WITH c AS (
    SELECT customer_unique_id, COUNT(DISTINCT order_id) AS orders, SUM(price) AS spend
    FROM fact_order_items WHERE is_revenue_item = 1 GROUP BY customer_unique_id)
SELECT CASE WHEN orders >= 2 THEN 'repeat' ELSE 'one-time' END AS type,
       COUNT(*) AS customers, ROUND(SUM(spend), 0) AS revenue,
       ROUND(100.0 * SUM(spend) / SUM(SUM(spend)) OVER (), 1) AS revenue_share_pct,
       ROUND(AVG(spend), 1) AS avg_spend_per_customer
FROM c GROUP BY type;
