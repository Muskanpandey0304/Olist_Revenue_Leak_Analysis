-- Star schema built from the staging tables. Run by pipeline/20_build_marts.py.

DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date AS
WITH RECURSIVE d(date) AS (
    SELECT DATE('2016-09-01') UNION ALL SELECT DATE(date, '+1 day') FROM d WHERE date < '2018-12-31')
SELECT d.date,
       CAST(STRFTIME('%Y', d.date) AS INTEGER) AS year,
       CAST(STRFTIME('%m', d.date) AS INTEGER) AS month,
       STRFTIME('%Y-%m', d.date) AS year_month,
       (CAST(STRFTIME('%m', d.date) AS INTEGER) + 2) / 3 AS quarter,
       CAST(STRFTIME('%w', d.date) AS INTEGER) AS weekday_num,   -- 0 = Sunday
       CASE WHEN STRFTIME('%w', d.date) IN ('0', '6') THEN 1 ELSE 0 END AS is_weekend,
       CASE WHEN h.date IS NULL THEN 0 ELSE 1 END AS is_holiday,
       h.holiday_name
FROM d LEFT JOIN stg_holidays h ON h.date = d.date;

DROP TABLE IF EXISTS dim_customer;
CREATE TABLE dim_customer AS
WITH ranked AS (
    SELECT c.customer_unique_id, c.customer_zip_code_prefix AS zip_prefix, c.customer_city AS city,
           c.customer_state AS state,
           ROW_NUMBER() OVER (PARTITION BY c.customer_unique_id
                              ORDER BY o.order_purchase_timestamp DESC) AS rn
    FROM stg_customers c JOIN stg_orders o ON o.customer_id = c.customer_id)
SELECT r.customer_unique_id, r.zip_prefix, r.city, r.state,
       s.region, s.population AS state_population, s.income_pc AS state_income_pc
FROM ranked r LEFT JOIN stg_ibge_states s ON s.state_code = r.state
WHERE r.rn = 1;   -- location of the customer's most recent order

DROP TABLE IF EXISTS dim_seller;
CREATE TABLE dim_seller AS
SELECT s.seller_id, s.seller_zip_code_prefix AS zip_prefix, s.seller_city AS city, s.seller_state AS state,
       g.lat, g.lng, i.region, i.population AS state_population, i.income_pc AS state_income_pc
FROM stg_sellers s
LEFT JOIN stg_geo_zip g ON g.zip_prefix = s.seller_zip_code_prefix
LEFT JOIN stg_ibge_states i ON i.state_code = s.seller_state;

DROP TABLE IF EXISTS dim_product;
CREATE TABLE dim_product AS
SELECT product_id, category, product_weight_g AS weight_g, product_length_cm AS length_cm,
       product_height_cm AS height_cm, product_width_cm AS width_cm,
       product_length_cm * product_height_cm * product_width_cm AS volume_cm3,
       product_photos_qty AS photos_qty
FROM stg_products;

DROP TABLE IF EXISTS fact_order_items;
CREATE TABLE fact_order_items AS
WITH base AS (
    SELECT i.order_id, i.order_item_id, i.product_id, i.seller_id, c.customer_unique_id,
           c.customer_state, o.order_status, o.purchase_date, o.in_window,
           CASE WHEN o.order_status = 'delivered' AND o.has_delivery_date = 1 THEN 1 ELSE 0 END AS is_delivered,
           i.price, i.freight_value,
           cg.lat AS c_lat, cg.lng AS c_lng, sl.lat AS s_lat, sl.lng AS s_lng
    FROM stg_order_items i
    JOIN stg_orders o ON o.order_id = i.order_id
    JOIN stg_customers c ON c.customer_id = o.customer_id
    LEFT JOIN stg_geo_zip cg ON cg.zip_prefix = c.customer_zip_code_prefix
    LEFT JOIN dim_seller sl ON sl.seller_id = i.seller_id)
SELECT order_id, order_item_id, product_id, seller_id, customer_unique_id, customer_state, order_status,
       purchase_date, in_window, is_delivered,
       CASE WHEN in_window = 1 AND is_delivered = 1 THEN 1 ELSE 0 END AS is_revenue_item,
       price, freight_value,
       CASE WHEN c_lat IS NULL OR s_lat IS NULL THEN NULL ELSE
            ROUND(2 * 6371 * ASIN(SQRT(
                POWER(SIN(RADIANS(c_lat - s_lat) / 2), 2) +
                COS(RADIANS(s_lat)) * COS(RADIANS(c_lat)) * POWER(SIN(RADIANS(c_lng - s_lng) / 2), 2))), 1)
       END AS distance_km
FROM base;

DROP TABLE IF EXISTS fact_orders;
CREATE TABLE fact_orders AS
WITH it AS (
    SELECT order_id, COUNT(*) AS n_items, COUNT(DISTINCT seller_id) AS n_sellers,
           SUM(price) AS items_price, SUM(freight_value) AS freight_total,
           AVG(distance_km) AS avg_distance_km, MAX(distance_km) AS max_distance_km
    FROM fact_order_items GROUP BY order_id),
pm AS (SELECT order_id, SUM(payment_value) AS paid_total, MAX(payment_installments) AS max_installments
       FROM stg_payments GROUP BY order_id),
pt AS (SELECT order_id, payment_type AS main_payment_type FROM (
           SELECT order_id, payment_type,
                  ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY payment_value DESC) AS rn
           FROM stg_payments) WHERE rn = 1)
SELECT o.order_id, c.customer_unique_id, c.customer_state, c.customer_zip_code_prefix AS customer_zip,
       o.order_status, o.purchase_date, o.order_purchase_timestamp, o.order_delivered_customer_date,
       o.order_estimated_delivery_date, o.in_window,
       CASE WHEN o.order_status = 'delivered' AND o.has_delivery_date = 1 THEN 1 ELSE 0 END AS is_delivered,
       CASE WHEN o.in_window = 1 AND o.order_status = 'delivered' AND o.has_delivery_date = 1
            THEN 1 ELSE 0 END AS is_revenue_order,
       o.delivery_days,
       CAST(JULIANDAY(o.order_estimated_delivery_date) - JULIANDAY(o.order_purchase_timestamp) AS INTEGER)
           AS estimated_days,
       o.is_late,
       (SELECT COUNT(*) FROM stg_holidays h
         WHERE h.date BETWEEN o.purchase_date AND SUBSTR(o.order_estimated_delivery_date, 1, 10))
           AS holidays_in_window,
       COALESCE(it.n_items, 0) AS n_items, it.n_sellers, it.items_price, it.freight_total,
       it.avg_distance_km, it.max_distance_km,
       pm.paid_total, pm.max_installments, pt.main_payment_type,
       r.review_score
FROM stg_orders o
JOIN stg_customers c ON c.customer_id = o.customer_id
LEFT JOIN it ON it.order_id = o.order_id
LEFT JOIN pm ON pm.order_id = o.order_id
LEFT JOIN pt ON pt.order_id = o.order_id
LEFT JOIN stg_reviews r ON r.order_id = o.order_id;

CREATE INDEX ix_fo_order ON fact_orders(order_id);
CREATE INDEX ix_fo_cust ON fact_orders(customer_unique_id);
CREATE INDEX ix_fo_date ON fact_orders(purchase_date);
CREATE INDEX ix_foi_order ON fact_order_items(order_id);
CREATE INDEX ix_foi_seller ON fact_order_items(seller_id);
CREATE INDEX ix_foi_product ON fact_order_items(product_id);
CREATE INDEX ix_dc_id ON dim_customer(customer_unique_id);
CREATE INDEX ix_dd_date ON dim_date(date);
