# Retail Analysis Skill

## When to use

当用户提出销售额、品类、门店、渠道、会员、库存相关的经营分析问题时使用。

典型问题：

- 最近7天华东区域销售额是否下降？
- 哪些品类对销售额下降贡献最大？
- 哪些门店或渠道拖累了整体增长？
- 库存是否可能影响销售表现？

## Required context

执行前必须阅读：

1. `semantic_layer/index.md`
2. `semantic_layer/business_wiki/metrics.md`
3. `semantic_layer/business_wiki/dimensions.md`
4. `semantic_layer/business_wiki/terms.md`
5. `semantic_layer/physical_wiki/tables.md`
6. `semantic_layer/physical_wiki/joins.md`

## Procedure

1. 明确分析目标、时间窗口、对比基准和核心指标。
2. 生成第一条 SQL，只回答"整体是否发生变化"。
3. 如果发生下降，按 `category_l1 -> store_name -> channel` 三个维度依次拆解贡献。
4. 每一步都输出 SQL、结果摘要和下一步判断。
5. 最终结论必须包含变化幅度、主要贡献因素、伴随现象、可复查 SQL 和风险提示。

## SQL rules

- GMV 必须使用 `SUM(pay_amount - refund_amount)`。
- 最近7天必须基于 `MAX(order_date)` 推导。
- 华东区域必须使用 `stores.region = '华东'`。
- 商品品类必须通过 `orders -> products` Join 获取。
- 门店区域必须通过 `orders -> stores` Join 获取。

## Guardrails

- 不允许直接使用字段名猜指标口径，必须引用 Business Wiki 中的指标定义。
- 不允许用系统当前日期推断最近7天。
- SQL 执行失败时，先检查 Physical Wiki，再修改 SQL。
- 不把相关性直接写成因果关系；结论中要标注"可能原因"和"需进一步验证"。

## Acceptance criteria

- 给出整体 current_gmv、previous_gmv、delta_gmv、delta_rate。
- 至少完成品类、门店、渠道三个维度的贡献拆解。
- 每个结论都能追溯到一条 SQL。
- 输出中明确说明引用的语义层文件。
