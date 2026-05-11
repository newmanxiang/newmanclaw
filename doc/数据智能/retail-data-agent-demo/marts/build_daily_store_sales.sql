DROP TABLE IF EXISTS daily_store_sales;

CREATE TABLE daily_store_sales AS
SELECT
    o.order_date AS biz_date,
    s.store_id,
    s.store_name,
    s.region,
    ROUND(SUM(o.pay_amount - o.refund_amount), 2) AS gmv,
    COUNT(DISTINCT o.order_id) AS order_count,
    ROUND(SUM(o.pay_amount - o.refund_amount) / COUNT(DISTINCT o.order_id), 2) AS aov,
    ROUND(SUM(o.pay_amount - o.refund_amount - p.cost_price * o.quantity), 2) AS gross_profit,
    ROUND(SUM(o.refund_amount), 2) AS refund_amount
FROM orders o
JOIN stores s ON o.store_id = s.store_id
JOIN products p ON o.sku_id = p.sku_id
GROUP BY
    o.order_date,
    s.store_id,
    s.store_name,
    s.region;
