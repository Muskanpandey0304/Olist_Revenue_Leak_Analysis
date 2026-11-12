-- Q3. Do customers come back? Cohort retention and a censoring-safe 90-day repeat rate.
-- Cohort = month of the customer's first delivered order inside the window.

-- 40a. Share of each cohort active again N months later (only months the data can observe)
WITH o AS (
    SELECT customer_unique_id, purchase_date,
           CAST(SUBSTR(purchase_date, 1, 4) AS INT) * 12 + CAST(SUBSTR(purchase_date, 6, 2) AS INT) AS m
    FROM fact_orders WHERE is_revenue_order = 1),
first AS (SELECT customer_unique_id, MIN(m) AS cohort_m FROM o GROUP BY customer_unique_id),
act AS (SELECT DISTINCT o.customer_unique_id, f.cohort_m, o.m - f.cohort_m AS age
        FROM o JOIN first f USING (customer_unique_id)),
size AS (SELECT cohort_m, COUNT(*) AS cohort_size FROM first GROUP BY cohort_m),
last_m AS (SELECT MAX(m) AS lm FROM o)
SELECT PRINTF('%d-%02d', (s.cohort_m - 1) / 12, (s.cohort_m - 1) % 12 + 1) AS cohort,
       s.cohort_size,
       CASE WHEN s.cohort_m + 1 <= l.lm THEN ROUND(100.0 * SUM(a.age = 1) / s.cohort_size, 2) END AS m1_pct,
       CASE WHEN s.cohort_m + 3 <= l.lm THEN ROUND(100.0 * SUM(a.age = 3) / s.cohort_size, 2) END AS m3_pct,
       CASE WHEN s.cohort_m + 6 <= l.lm THEN ROUND(100.0 * SUM(a.age = 6) / s.cohort_size, 2) END AS m6_pct,
       CASE WHEN s.cohort_m + 12 <= l.lm THEN ROUND(100.0 * SUM(a.age = 12) / s.cohort_size, 2) END AS m12_pct
FROM size s JOIN act a USING (cohort_m), last_m l
GROUP BY s.cohort_m ORDER BY s.cohort_m;

-- 40b. Repeat within 90 days of the first order, for customers whose first order is at least
--      90 days before the end of the data (everyone had the same chance to come back).
WITH ord AS (
    SELECT customer_unique_id, purchase_date,
           ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY order_purchase_timestamp) AS n
    FROM fact_orders WHERE is_revenue_order = 1),
f AS (SELECT customer_unique_id, purchase_date AS d1 FROM ord WHERE n = 1),
s AS (SELECT customer_unique_id, purchase_date AS d2 FROM ord WHERE n = 2)
SELECT COUNT(*) AS customers_observed,
       SUM(s.d2 IS NOT NULL AND JULIANDAY(s.d2) - JULIANDAY(f.d1) <= 90) AS repeated_within_90d,
       ROUND(100.0 * SUM(s.d2 IS NOT NULL AND JULIANDAY(s.d2) - JULIANDAY(f.d1) <= 90) / COUNT(*), 2) AS repeat_90d_pct,
       ROUND(100.0 * SUM(s.d2 IS NOT NULL) / COUNT(*), 2) AS ever_repeated_pct
FROM f LEFT JOIN s USING (customer_unique_id)
WHERE f.d1 <= DATE('2018-08-31', '-90 day');
