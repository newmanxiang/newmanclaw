# Metrics

## GMV

- 中文名：成交金额
- 业务定义：用户实际支付的商品金额，需扣除退款金额
- SQL口径：`SUM(orders.pay_amount - orders.refund_amount)`
- 默认时间字段：`orders.order_date`
- 可分析维度：`region`, `city`, `store_type`, `store_name`, `category_l1`, `category_l2`, `channel`
- 注意事项：取消订单不进入 `orders`；退款按订单行上的 `refund_amount` 扣减

## order_count

- 中文名：订单数
- 业务定义：去重后的订单数量
- SQL口径：`COUNT(DISTINCT orders.order_id)`
- 默认时间字段：`orders.order_date`
- 注意事项：`orders` 是订单商品行粒度，一笔订单购买多个商品会有多行，必须去重

## AOV

- 中文名：客单价
- 业务定义：每笔订单平均成交金额
- SQL口径：`SUM(orders.pay_amount - orders.refund_amount) / COUNT(DISTINCT orders.order_id)`
- 默认时间字段：`orders.order_date`

## gross_profit

- 中文名：毛利额
- 业务定义：成交金额扣除商品成本后的金额
- SQL口径：`SUM(orders.pay_amount - orders.refund_amount - products.cost_price * orders.quantity)`
- 默认时间字段：`orders.order_date`
- 必要Join：`orders.sku_id = products.sku_id`

## refund_amount

- 中文名：退款金额
- 业务定义：订单行上的退款金额
- SQL口径：`SUM(orders.refund_amount)`
- 默认时间字段：`orders.order_date`

## repurchase_member_count

- 中文名：复购会员数
- 业务定义：统计周期内下单次数大于等于2次的会员数
- SQL口径：先按 `member_id` 聚合 `COUNT(DISTINCT order_id)`，再统计订单数大于等于2的会员
- 默认时间字段：`orders.order_date`
