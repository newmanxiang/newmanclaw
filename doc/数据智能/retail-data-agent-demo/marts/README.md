# Marts

## daily_store_sales

每日门店经营汇总表，粒度为 `biz_date + store_id`。

### 生成方式

```bash
python3 scripts/build_daily_store_sales.py
```

### 字段口径

| 字段 | 说明 |
|------|------|
| `biz_date` | 业务日期，来自 `orders.order_date` |
| `store_id` | 门店ID |
| `store_name` | 门店名称 |
| `region` | 大区 |
| `gmv` | `SUM(pay_amount - refund_amount)` |
| `order_count` | `COUNT(DISTINCT order_id)` |
| `aov` | `gmv / order_count` |
| `gross_profit` | `SUM(pay_amount - refund_amount - cost_price * quantity)` |
| `refund_amount` | `SUM(refund_amount)` |

### 质量检查

- `biz_date + store_id` 不重复
- 核心指标非空
- 金额类指标不为负
