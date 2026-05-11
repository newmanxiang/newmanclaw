# Retail Data Agent Demo

这个 Demo 用一个通用的零售订单经营分析场景，演示 Claude Code 如何从"只会查库"逐步升级为"会按语义层和 Skill 做数据工作"。

## 1. 快速开始

```bash
python3 scripts/init_db.py
python3 scripts/run_query.py "SELECT COUNT(*) AS order_lines FROM orders"
python3 scripts/build_daily_store_sales.py
```

初始化脚本会自动生成：

- `data/seed/*.csv`：订单、商品、门店、会员、库存快照种子数据
- `data/retail.db`：SQLite 演示数据库
- `daily_store_sales`：由数据开发脚本生成的每日门店经营汇总表

## 2. Demo主线

核心问题：

> 最近7天华东区域销售额下降了吗？如果下降，主要是哪些品类、门店和渠道造成的？请给出可复查的SQL和结论。

这个问题需要 Agent 同时理解：

- 销售额使用 GMV 口径：`SUM(pay_amount - refund_amount)`
- 最近7天以数据中最大 `order_date` 为结束日期
- 华东区域来自 `stores.region = '华东'`
- 下钻路径按品类、门店、渠道逐层拆解

## 3. 建议演示顺序

### 第1轮：无语义层，直接提问

```text
请分析最近7天华东区域销售额是否下降。
如果下降，请说明主要由哪些品类、门店和渠道造成。
```

观察点：Claude Code 可能猜错销售额口径、时间窗口或 Join 路径。

### 第2轮：先读两层语义层

```text
请先阅读 semantic_layer/index.md，再分析最近7天华东区域销售额是否下降。
如果下降，请说明主要由哪些品类、门店和渠道造成。
所有SQL必须引用语义层中的口径，并给出可复查SQL。
```

观察点：SQL 应使用 GMV 口径、华东区域过滤和数据最大日期。

### 第3轮：引入经营分析 Skill

```text
请使用 skills/retail-analysis-skill.md。
按Skill流程分析最近7天华东区域GMV下降原因。
每一步都输出SQL、结果摘要和下一步判断。
```

观察点：Claude Code 应按整体判断、品类拆解、门店拆解、渠道拆解的顺序执行。

### 第4轮：引入数据开发 Skill

```text
请使用 skills/data-development-skill.md。
基于语义层开发每日门店经营汇总表 daily_store_sales。
字段包含 biz_date、store_id、store_name、region、gmv、order_count、aov、gross_profit、refund_amount。
要求生成可重复执行脚本，运行质量检查，并展示样例结果。
```

观察点：数据开发任务需要脚本、目标表、质量检查和开发说明，不能只输出一段 SQL。

## 4. 预置命令

运行下降判断查询：

```bash
python3 scripts/run_query.py "$(cat scripts/demo_sales_decline_query.sql)"
```

验证任意 SQL 文件：

```bash
python3 scripts/validate_sql.py scripts/demo_sales_decline_query.sql
```

重建汇总表：

```bash
python3 scripts/build_daily_store_sales.py
```

## 5. 知识资产说明

| 目录 | 作用 |
|------|------|
| `semantic_layer/business_wiki` | 指标、维度、术语等业务语义 |
| `semantic_layer/physical_wiki` | 表、字段、Join 等物理语义 |
| `skills/retail-analysis-skill.md` | 经营分析任务 SOP |
| `skills/data-development-skill.md` | 数据开发任务 SOP |
| `marts/` | 汇总表开发脚本和说明 |

一句话：语义层告诉 Agent "怎么算、在哪里"，Skill 告诉 Agent "按什么流程做"。
