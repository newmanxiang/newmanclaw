# Tables

## orders

- 中文名：订单事实表
- 粒度：订单商品行，一笔订单购买多个商品时会有多行
- 主键：`order_id + sku_id`
- 时间字段：`order_date`
- 主要用途：销售、退款、渠道、会员行为分析

## products

- 中文名：商品维表
- 粒度：商品 SKU
- 主键：`sku_id`
- 主要用途：补充商品名称、一级品类、二级品类、标价、成本价

## stores

- 中文名：门店维表
- 粒度：门店
- 主键：`store_id`
- 主要用途：补充门店名称、城市、大区、门店类型

## members

- 中文名：会员维表
- 粒度：会员
- 主键：`member_id`
- 主要用途：补充会员等级、会员注册日期、会员城市

## inventory_snapshot

- 中文名：库存快照表
- 粒度：日期 + 门店 + 商品
- 主键：`snapshot_date + store_id + sku_id`
- 时间字段：`snapshot_date`
- 主要用途：库存、缺货、周转分析

## daily_store_sales

- 中文名：每日门店经营汇总表
- 粒度：日期 + 门店
- 主键：`biz_date + store_id`
- 生成脚本：`marts/build_daily_store_sales.sql`
- 主要用途：门店经营看板、区域销售趋势分析
