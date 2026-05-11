# Data Development Skill

## When to use

当用户要求新增汇总表、开发指标宽表、生成 ETL 脚本、校验数据质量时使用。

典型问题：

- 开发每日门店经营汇总表。
- 把 GMV、订单数、客单价、毛利额沉淀成可复用宽表。
- 为经营分析看板准备一张按日聚合的 mart 表。

## Required context

执行前必须阅读：

1. `semantic_layer/index.md`
2. `semantic_layer/business_wiki/metrics.md`
3. `semantic_layer/physical_wiki/tables.md`
4. `semantic_layer/physical_wiki/columns.md`
5. `semantic_layer/physical_wiki/joins.md`

## Procedure

1. 读取业务指标定义，确认目标表粒度和字段口径。
2. 设计目标表 Schema，并写入 `marts/README.md`。
3. 编写可重复执行的 SQL 或 Python 脚本。
4. 运行脚本生成目标表。
5. 增加最小数据质量检查：主键唯一、核心指标非空、金额不为负。
6. 展示样例结果。
7. 输出开发说明：输入表、输出表、调度建议、质量规则。

## Guardrails

- 生成的派生表字段必须能追溯到语义层定义。
- 不允许只给伪代码，必须生成可运行脚本。
- 对金额类指标必须说明是否扣减退款。
- 对订单事实表聚合时，订单数必须使用 `COUNT(DISTINCT order_id)`。
- 目标表重跑时必须可覆盖旧结果，避免重复写入。

## Acceptance criteria

- 存在可运行脚本或 SQL 文件。
- 目标表可在 SQLite 中查询。
- 质量检查全部通过。
- README 中说明字段口径和生成方式。
