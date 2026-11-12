-- Q1. Which categories carry the revenue? Rank, share and cumulative share (Pareto)
WITH cat AS (
    SELECT p.category, ROUND(SUM(i.price), 0) AS revenue, COUNT(DISTINCT i.order_id) AS orders
    FROM fact_order_items i JOIN dim_product p ON p.product_id = i.product_id
    WHERE i.is_revenue_item = 1 GROUP BY p.category),
ranked AS (
    SELECT category, revenue, orders,
           RANK() OVER (ORDER BY revenue DESC) AS rnk,
           ROUND(100.0 * revenue / SUM(revenue) OVER (), 1) AS share_pct,
           ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC) / SUM(revenue) OVER (), 1) AS cumulative_pct
    FROM cat)
SELECT * FROM ranked WHERE rnk <= 12 ORDER BY rnk;

-- How many categories make up 80% of revenue?
WITH cat AS (
    SELECT p.category, SUM(i.price) AS revenue
    FROM fact_order_items i JOIN dim_product p ON p.product_id = i.product_id
    WHERE i.is_revenue_item = 1 GROUP BY p.category),
c AS (SELECT category, 100.0 * SUM(revenue) OVER (ORDER BY revenue DESC) / SUM(revenue) OVER () AS cum FROM cat)
SELECT COUNT(*) AS categories_total,
       (SELECT COUNT(*) FROM c WHERE cum <= 80) + 1 AS categories_to_reach_80pct
FROM c;
