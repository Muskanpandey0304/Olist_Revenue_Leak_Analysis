-- Q1. Where do customers sit, and how do they pay?
SELECT customer_state, ROUND(SUM(price), 0) AS revenue,
       ROUND(100.0 * SUM(price) / SUM(SUM(price)) OVER (), 1) AS share_pct,
       COUNT(DISTINCT order_id) AS orders
FROM fact_order_items WHERE is_revenue_item = 1
GROUP BY customer_state ORDER BY revenue DESC LIMIT 8;

SELECT main_payment_type, COUNT(*) AS orders,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct,
       ROUND(AVG(items_price), 1) AS avg_items_price
FROM fact_orders WHERE is_revenue_order = 1 GROUP BY main_payment_type ORDER BY orders DESC;
