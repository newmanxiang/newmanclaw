# Joins

## orders -> products

- Join Key：`orders.sku_id = products.sku_id`
- Join Type：`JOIN` 或 `LEFT JOIN`
- 用途：补充商品名称、品类、成本价、标价
- 常见指标：GMV按品类拆解、毛利额

## orders -> stores

- Join Key：`orders.store_id = stores.store_id`
- Join Type：`JOIN` 或 `LEFT JOIN`
- 用途：补充门店名称、城市、大区、门店类型
- 常见指标：GMV按区域、城市、门店拆解

## orders -> members

- Join Key：`orders.member_id = members.member_id`
- Join Type：`LEFT JOIN`
- 用途：补充会员等级、会员城市
- 常见指标：复购会员数、会员等级销售贡献

## inventory_snapshot -> products

- Join Key：`inventory_snapshot.sku_id = products.sku_id`
- Join Type：`JOIN` 或 `LEFT JOIN`
- 用途：库存按品类分析

## inventory_snapshot -> stores

- Join Key：`inventory_snapshot.store_id = stores.store_id`
- Join Type：`JOIN` 或 `LEFT JOIN`
- 用途：库存按区域、城市、门店分析
