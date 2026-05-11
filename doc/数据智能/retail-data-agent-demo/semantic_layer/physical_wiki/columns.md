# Columns

## orders

| 字段 | 类型 | 含义 |
|------|------|------|
| `order_id` | TEXT | 订单ID |
| `order_date` | TEXT | 订单日期，格式为 `YYYY-MM-DD` |
| `store_id` | TEXT | 门店ID |
| `member_id` | TEXT | 会员ID |
| `sku_id` | TEXT | 商品SKU |
| `quantity` | INTEGER | 商品件数 |
| `pay_amount` | REAL | 用户支付金额，未扣退款 |
| `refund_amount` | REAL | 订单行退款金额 |
| `channel` | TEXT | 销售渠道 |

## products

| 字段 | 类型 | 含义 |
|------|------|------|
| `sku_id` | TEXT | 商品SKU |
| `sku_name` | TEXT | 商品名称 |
| `category_l1` | TEXT | 一级品类 |
| `category_l2` | TEXT | 二级品类 |
| `list_price` | REAL | 商品标价 |
| `cost_price` | REAL | 商品单位成本 |

## stores

| 字段 | 类型 | 含义 |
|------|------|------|
| `store_id` | TEXT | 门店ID |
| `store_name` | TEXT | 门店名称 |
| `city` | TEXT | 门店所在城市 |
| `region` | TEXT | 门店所属大区 |
| `store_type` | TEXT | 门店类型 |
| `open_date` | TEXT | 开业日期 |

## members

| 字段 | 类型 | 含义 |
|------|------|------|
| `member_id` | TEXT | 会员ID |
| `join_date` | TEXT | 入会日期 |
| `member_level` | TEXT | 会员等级 |
| `city` | TEXT | 会员城市 |

## inventory_snapshot

| 字段 | 类型 | 含义 |
|------|------|------|
| `snapshot_date` | TEXT | 库存快照日期 |
| `store_id` | TEXT | 门店ID |
| `sku_id` | TEXT | 商品SKU |
| `on_hand_qty` | INTEGER | 账面库存 |
| `available_qty` | INTEGER | 可售库存 |
