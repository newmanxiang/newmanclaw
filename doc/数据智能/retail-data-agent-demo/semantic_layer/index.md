# Semantic Layer Index

这是 Claude Code 在回答零售数据问题前应优先阅读的入口文件。

## 读取顺序

| 用户意图 | 先读 | 再读 |
|----------|------|------|
| 查询销售额、订单数、客单价、毛利 | `business_wiki/metrics.md` | `physical_wiki/tables.md`, `physical_wiki/joins.md` |
| 查询区域、城市、门店、渠道、品类 | `business_wiki/dimensions.md` | `physical_wiki/columns.md` |
| 判断"最近7天"、"下降"、"线上渠道" | `business_wiki/terms.md` | `business_wiki/dimensions.md` |
| 开发汇总表或指标宽表 | `business_wiki/metrics.md` | `physical_wiki/tables.md`, `physical_wiki/joins.md`, `physical_wiki/columns.md` |

## 默认规则

1. 不直接猜指标口径，先查 `business_wiki/metrics.md`。
2. 不直接猜字段位置，先查 `physical_wiki/tables.md` 和 `physical_wiki/columns.md`。
3. 涉及跨表查询时，必须使用 `physical_wiki/joins.md` 中定义的 Join。
4. "最近N天"以数据中最大业务日期为结束日期，不使用系统当天日期。
5. 输出 SQL 时说明引用了哪些语义层定义。
