-- Q1. Monthly trend with month-over-month growth (LAG window function)
WITH monthly AS (
    SELECT d.year_month,
           ROUND(SUM(i.price), 0)                              AS revenue,
           COUNT(DISTINCT i.order_id)                          AS orders,
           COUNT(DISTINCT i.customer_unique_id)                AS active_customers,
           ROUND(SUM(i.price) / COUNT(DISTINCT i.order_id), 2) AS aov
    FROM fact_order_items i JOIN dim_date d ON d.date = i.purchase_date
    WHERE i.is_revenue_item = 1
    GROUP BY d.year_month)
SELECT year_month, revenue, orders, active_customers, aov,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY year_month))
             / LAG(revenue) OVER (ORDER BY year_month), 1) AS revenue_mom_pct,
       ROUND(100.0 * (orders - LAG(orders) OVER (ORDER BY year_month))
             / LAG(orders) OVER (ORDER BY year_month), 1)  AS orders_mom_pct
FROM monthly ORDER BY year_month;
