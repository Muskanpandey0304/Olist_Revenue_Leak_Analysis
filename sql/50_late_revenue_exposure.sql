-- Q4. How much revenue is tied to a bad delivery experience?
SELECT CASE WHEN is_late = 0 THEN 'on time'
            WHEN delivery_days - estimated_days >= 7 THEN 'late 7+ days'
            ELSE 'late 1-6 days' END AS delivery,
       COUNT(*) AS orders, ROUND(SUM(items_price), 0) AS revenue,
       ROUND(100.0 * SUM(items_price) / SUM(SUM(items_price)) OVER (), 2) AS revenue_share_pct,
       ROUND(AVG(review_score), 2) AS avg_review
FROM fact_orders WHERE is_revenue_order = 1 GROUP BY delivery ORDER BY orders;
