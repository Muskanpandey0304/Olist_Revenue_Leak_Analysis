SELECT COUNT(*) AS items, SUM(distance_km IS NULL) AS no_distance, MIN(distance_km) AS min_km,
       ROUND(AVG(distance_km),0) AS avg_km, MAX(distance_km) AS max_km, SUM(distance_km > 4500) AS over_4500km
FROM fact_order_items;
SELECT COUNT(*) AS sellers, SUM(lat IS NULL) AS no_location,
       SUM(lat NOT BETWEEN -34 AND 6 OR lng NOT BETWEEN -74 AND -34) AS outside_brazil
FROM dim_seller;
SELECT ROUND(SUM(price),2) AS revenue_window, COUNT(DISTINCT order_id) AS orders
FROM fact_order_items WHERE is_revenue_item = 1;
SELECT SUM(state_population IS NULL) AS customers_without_ibge FROM dim_customer;
