# Dimensions

## region

- 中文名：大区
- 来源字段：`stores.region`
- 常用取值：华东、华北、华南、西南
- 过滤规则：用户说"华东区域"时，使用 `stores.region = '华东'`

## city

- 中文名：城市
- 来源字段：`stores.city` 或 `members.city`
- 默认选择：分析门店经营时使用 `stores.city`；分析会员来源时使用 `members.city`

## store_type

- 中文名：门店类型
- 来源字段：`stores.store_type`
- 常用取值：旗舰店、标准店

## category_l1

- 中文名：一级品类
- 来源字段：`products.category_l1`
- 常用取值：饮品、烘焙、零食、日化、家居

## category_l2

- 中文名：二级品类
- 来源字段：`products.category_l2`
- 示例取值：咖啡、果汁、面包、蛋糕、洗护、收纳

## channel

- 中文名：销售渠道
- 来源字段：`orders.channel`
- 常用取值：门店、App、小程序、外卖平台
- 归类规则：线上渠道 = App + 小程序 + 外卖平台；线下渠道 = 门店

## member_level

- 中文名：会员等级
- 来源字段：`members.member_level`
- 常用取值：普通、银卡、金卡、黑金
