WITH max_date AS (
    SELECT MAX(order_date) AS end_date
    FROM orders
),
period_orders AS (
    SELECT
        CASE
            WHEN o.order_date BETWEEN date(m.end_date, '-6 day') AND m.end_date THEN 'current_7d'
            WHEN o.order_date BETWEEN date(m.end_date, '-13 day') AND date(m.end_date, '-7 day') THEN 'previous_7d'
        END AS period_name,
        p.category_l1,
        s.store_name,
        o.channel,
        SUM(o.pay_amount - o.refund_amount) AS gmv
    FROM orders o
    JOIN stores s ON o.store_id = s.store_id
    JOIN products p ON o.sku_id = p.sku_id
    CROSS JOIN max_date m
    WHERE s.region = '华东'
      AND o.order_date BETWEEN date(m.end_date, '-13 day') AND m.end_date
    GROUP BY period_name, p.category_l1, s.store_name, o.channel
),
summary AS (
    SELECT
        period_name,
        ROUND(SUM(gmv), 2) AS gmv
    FROM period_orders
    WHERE period_name IS NOT NULL
    GROUP BY period_name
),
category_delta AS (
    SELECT
        category_l1,
        ROUND(SUM(CASE WHEN period_name = 'current_7d' THEN gmv ELSE 0 END), 2) AS current_gmv,
        ROUND(SUM(CASE WHEN period_name = 'previous_7d' THEN gmv ELSE 0 END), 2) AS previous_gmv,
        ROUND(SUM(CASE WHEN period_name = 'current_7d' THEN gmv ELSE -gmv END), 2) AS delta_gmv
    FROM period_orders
    WHERE period_name IS NOT NULL
    GROUP BY category_l1
),
store_delta AS (
    SELECT
        store_name,
        ROUND(SUM(CASE WHEN period_name = 'current_7d' THEN gmv ELSE 0 END), 2) AS current_gmv,
        ROUND(SUM(CASE WHEN period_name = 'previous_7d' THEN gmv ELSE 0 END), 2) AS previous_gmv,
        ROUND(SUM(CASE WHEN period_name = 'current_7d' THEN gmv ELSE -gmv END), 2) AS delta_gmv
    FROM period_orders
    WHERE period_name IS NOT NULL
    GROUP BY store_name
),
channel_delta AS (
    SELECT
        channel,
        ROUND(SUM(CASE WHEN period_name = 'current_7d' THEN gmv ELSE 0 END), 2) AS current_gmv,
        ROUND(SUM(CASE WHEN period_name = 'previous_7d' THEN gmv ELSE 0 END), 2) AS previous_gmv,
        ROUND(SUM(CASE WHEN period_name = 'current_7d' THEN gmv ELSE -gmv END), 2) AS delta_gmv
    FROM period_orders
    WHERE period_name IS NOT NULL
    GROUP BY channel
)
SELECT
    'overall' AS section,
    period_name AS item,
    gmv AS current_gmv,
    NULL AS previous_gmv,
    NULL AS delta_gmv
FROM summary
UNION ALL
SELECT
    'category_delta' AS section,
    category_l1 AS item,
    current_gmv,
    previous_gmv,
    delta_gmv
FROM category_delta
UNION ALL
SELECT
    'store_delta' AS section,
    store_name AS item,
    current_gmv,
    previous_gmv,
    delta_gmv
FROM store_delta
UNION ALL
SELECT
    'channel_delta' AS section,
    channel AS item,
    current_gmv,
    previous_gmv,
    delta_gmv
FROM channel_delta
ORDER BY section, delta_gmv;
