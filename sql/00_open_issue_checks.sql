-- Issue 4: status of orders with no items
SELECT o.order_status, COUNT(*) AS orders
FROM stg_orders o LEFT JOIN stg_order_items i ON i.order_id = o.order_id
WHERE i.order_id IS NULL
GROUP BY o.order_status ORDER BY orders DESC;

-- Issue 7: payments vs items + freight, by order status (orders that have items)
WITH it AS (SELECT order_id, SUM(price + freight_value) AS item_total FROM stg_order_items GROUP BY order_id),
     pm AS (SELECT order_id, SUM(payment_value) AS paid FROM stg_payments GROUP BY order_id)
SELECT o.order_status,
       COUNT(*) AS orders,
       ROUND(SUM(it.item_total), 0) AS items_plus_freight,
       ROUND(SUM(pm.paid), 0) AS paid,
       SUM(ABS(pm.paid - it.item_total) > 0.05) AS mismatched_orders
FROM stg_orders o JOIN it ON it.order_id = o.order_id LEFT JOIN pm ON pm.order_id = o.order_id
GROUP BY o.order_status ORDER BY orders DESC;

-- Issue 7 detail: mismatches among delivered orders, split by payment type mix
WITH it AS (SELECT order_id, SUM(price + freight_value) AS item_total FROM stg_order_items GROUP BY order_id),
     pm AS (SELECT order_id, SUM(payment_value) AS paid, MAX(payment_installments) AS max_inst,
                   COUNT(*) AS n_pay FROM stg_payments GROUP BY order_id)
SELECT CASE WHEN pm.paid > it.item_total THEN 'paid more' ELSE 'paid less' END AS direction,
       COUNT(*) AS orders, ROUND(AVG(pm.max_inst), 1) AS avg_max_installments,
       ROUND(SUM(pm.paid - it.item_total), 0) AS net_gap
FROM stg_orders o JOIN it ON it.order_id = o.order_id JOIN pm ON pm.order_id = o.order_id
WHERE o.order_status = 'delivered' AND ABS(pm.paid - it.item_total) > 0.05
GROUP BY direction;
