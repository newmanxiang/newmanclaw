# CarbonData + HetuEngine 对比 Iceberg + StarRocks 湖仓一体架构深度分析

> **对比对象**：
> - **架构 A**：CarbonData（湖内存储格式）+ HetuEngine（联邦/MPP 查询引擎）
> - **架构 B**：Iceberg（开放表格式）+ StarRocks（通过 External Catalog 外表与湖内数据连接）
>
> **对比维度**：存储格式 · 查询效率 · 加速方式
> **更新日期**：2026 年 6 月（结合电信运维 XDR 观测数据场景修订）
> **核心问题**：在"存储格式 / 查询效率 / 加速方式"三个维度上，"私有列存格式 + 联邦引擎"路线（CarbonData+Hetu）与"开放表格式 + 向量化 MPP 外表"路线（Iceberg+StarRocks）各自的工作机制、性能边界与适用场景是什么？
> **重点场景**：电信运维类数据（网络观测数据，如 XDR / 话单 / 信令 / KPI）具有 **Append-only（无更新）** 与 **数十亿级 XDR 点查 + 多维查询** 两大特征，本轮修订专门评估这两点对架构选型的影响（详见第八章）。

---

## 目录

- [一、核心结论摘要](#一核心结论摘要)
- [二、两种架构总览](#二两种架构总览)
  - [2.1 架构 A：CarbonData + HetuEngine](#21-架构-acarbondata--hetuengine)
  - [2.2 架构 B：Iceberg + StarRocks（External Catalog 外表）](#22-架构-biceberg--starrocksexternal-catalog-外表)
  - [2.3 两条技术路线的本质差异](#23-两条技术路线的本质差异)
- [三、维度一：存储格式深度对比](#三维度一存储格式深度对比)
  - [3.1 CarbonData：列存文件格式 + 重型内建索引](#31-carbondata列存文件格式--重型内建索引)
  - [3.2 Iceberg：表格式（Table Format）+ Parquet/ORC 数据文件](#32-iceberg表格式table-format--parquetorc-数据文件)
  - [3.3 存储格式维度对比表](#33-存储格式维度对比表)
- [四、维度二：查询效率深度对比](#四维度二查询效率深度对比)
  - [4.1 HetuEngine 查询 CarbonData 的执行链路](#41-hetuengine-查询-carbondata-的执行链路)
  - [4.2 StarRocks 查询 Iceberg 的执行链路](#42-starrocks-查询-iceberg-的执行链路)
  - [4.3 查询效率维度对比表](#43-查询效率维度对比表)
  - [4.4 不同查询负载下的效率画像](#44-不同查询负载下的效率画像)
- [五、维度三：加速方式深度对比](#五维度三加速方式深度对比)
  - [5.1 架构 A 的加速手段](#51-架构-a-的加速手段)
  - [5.2 架构 B 的加速手段](#52-架构-b-的加速手段)
  - [5.3 加速方式维度对比表](#53-加速方式维度对比表)
- [六、综合对比矩阵](#六综合对比矩阵)
- [七、选型建议与适用场景](#七选型建议与适用场景)
- [八、电信运维（XDR）场景下的再评估](#八电信运维xdr场景下的再评估)
  - [8.1 场景特征：Append-only + 数十亿 XDR 点查/多维查询](#81-场景特征append-only--数十亿-xdr-点查多维查询)
  - [8.2 特征一影响：Append-only 使开放表格式的 ACID 增益有限](#82-特征一影响append-only-使开放表格式的-acid-增益有限)
  - [8.3 特征二影响：数十亿 XDR 点查 / 多维查询的效率分水岭](#83-特征二影响数十亿-xdr-点查--多维查询的效率分水岭)
  - [8.4 三维度在电信运维场景下的结论修正](#84-三维度在电信运维场景下的结论修正)
  - [8.5 电信运维场景选型建议](#85-电信运维场景选型建议)
- [九、演进趋势研判](#九演进趋势研判)
- [附录：参考来源索引](#附录参考来源索引)

---

## 一、核心结论摘要

| 维度 | 架构 A：CarbonData + HetuEngine | 架构 B：Iceberg + StarRocks | 结论倾向 |
|------|------------------------------|---------------------------|---------|
| **存储格式定位** | 一体化"列存文件 + 内建多级索引 + DataMap 预聚合"私有格式 | 开放"表格式（元数据层）+ Parquet/ORC 数据文件"分层格式 | 各有侧重：A 重查询、B 重开放与演进 |
| **存储能力强项** | 多级索引、全局字典、Sort/二级/时空索引、内建预聚合 | Schema 演进、隐藏分区、Snapshot/Time Travel、ACID、MOR/COW | A 强在"读优化"，B 强在"表管理与演进" |
| **查询引擎** | HetuEngine（Trino 衍生，JVM，联邦 + 计算下推） | StarRocks（C++ 全向量化 MPP，External Catalog） | B 在交互式 OLAP 上吞吐/延迟普遍占优 |
| **查询效率（湖上即席）** | 中—高（依赖 CarbonData 索引裁剪 + Hetu 下推） | 高（向量化 + Data Cache + 物化视图重写） | **B 占优** |
| **加速方式** | 格式内建索引/预聚合为主 + 引擎侧 CTE/元数据缓存、计算下推 | 引擎侧 Data Cache + 异步物化视图 + 查询重写为主 + 格式侧裁剪 | A "加速沉到存储"，B "加速沉到引擎" |
| **开放性 / 生态** | 私有格式，主要绑定 Spark/Presto-Hetu，社区弱化 | 开放标准，被 Spark/Flink/Trino/StarRocks/Snowflake 等广泛支持 | **B 占优** |
| **最佳场景** | 只读 + 多维 OLAP + 时空分析（如电信网络观测） | 通用湖仓即席分析、实时 BI、需要 Schema 演进/事务的表 | 场景决定，见第七章 |

**三句话结论**：

1. **存储格式层面**——CarbonData 是"把索引和预聚合打进文件里"的重型列存格式，强在读优化与时空/多维查询；Iceberg 是"表格式 + 标准列存数据文件"的开放分层设计，强在 Schema 演进、快照隔离、事务与跨引擎互操作。
2. **查询效率层面**——HetuEngine 是 JVM 系联邦引擎，靠 CarbonData 的内建索引做裁剪、靠下推减少数据搬运；StarRocks 是 C++ 全向量化 MPP，叠加本地 Data Cache 与物化视图查询重写，在交互式 OLAP 的延迟与并发上通常领先。
3. **加速方式层面**——两者的根本差异是"加速能力放在哪一层"：架构 A 把加速沉淀进**存储格式**（多级索引、字典、DataMap），架构 B 把加速沉淀进**计算引擎**（Data Cache、物化视图、向量化），后者更解耦、更易随引擎升级而持续增强。

> **电信运维场景速读（详见第八章）**：当数据是 **Append-only 的网络观测数据（XDR/话单/信令/KPI）** 且查询是 **数十亿 XDR 的点查与多维查询** 时，上面"B 在通用场景普遍占优"的结论需要**显著修正**——
> - 开放表格式（Iceberg）赖以差异化的 **ACID / MOR / Time Travel / 行级更新** 在 Append-only 下**增益有限**，几乎用不上；
> - 数十亿 XDR 的**高基数点查**强依赖二级索引、**多维查询**强依赖多级/排序/时空索引，这正是 **CarbonData 的核心长板**，而 Iceberg+StarRocks 缺少原生二级/时空索引、需靠扫描或物化视图弥补；
> - 因此在该限定场景下，**架构 A（CarbonData + HetuEngine）在存储格式与查询效率两个维度上反超**，架构 B 的优势收敛为"开放生态与引擎演进速度"。

---

## 二、两种架构总览

### 2.1 架构 A：CarbonData + HetuEngine

```
┌──────────────────────────────────────────────┐
│                  应用 / BI 层                  │
└───────────────────────┬──────────────────────┘
                        │ 标准 SQL
┌───────────────────────▼──────────────────────┐
│              HetuEngine（查询引擎）            │
│   - Trino/Presto 衍生，Coordinator + Worker    │
│   - 联邦查询 / 计算下推 / CTE 缓存             │
│   - 元数据缓存 / 物化视图                       │
└───────────────────────┬──────────────────────┘
                        │ Connector 读取
┌───────────────────────▼──────────────────────┐
│           CarbonData（湖内存储格式）           │
│   列存文件 + 多级索引 + 全局字典 + DataMap     │
│   ┌────────────┐ ┌────────────┐ ┌──────────┐  │
│   │ Block 索引 │ │ Blocklet索引│ │二级/空间 │  │
│   └────────────┘ └────────────┘ └──────────┘  │
└───────────────────────┬──────────────────────┘
                        │
┌───────────────────────▼──────────────────────┐
│            HDFS / OBS / S3（对象存储）         │
└──────────────────────────────────────────────┘
```

**关键特征**：

- **CarbonData** 是华为贡献给 Apache 的列式存储格式，核心定位是"列存文件 + 伴随索引"。它把多级索引（Block/Blocklet/Page）、全局字典编码、Sort Columns、二级索引、时空索引、Timeseries/预聚合 DataMap 等加速能力**直接编进文件格式与表元数据**。
- **HetuEngine** 是华为基于 Trino/Presto 演进的联邦查询与数据虚拟化引擎（JVM 实现），通过 Connector 读取 CarbonData，并提供计算下推、CTE 缓存、元数据缓存、物化视图等引擎侧能力。它也能跨源协同查询 Hive/HBase/GaussDB/ClickHouse 等。
- **加速重心**：落在**存储格式自身**。引擎主要负责"把谓词/投影/聚合下推给 CarbonData，让格式的索引发挥作用"。

### 2.2 架构 B：Iceberg + StarRocks（External Catalog 外表）

```
┌──────────────────────────────────────────────┐
│                  应用 / BI 层                  │
└───────────────────────┬──────────────────────┘
                        │ 标准 SQL
┌───────────────────────▼──────────────────────┐
│            StarRocks FE（前端 / 优化器）       │
│   解析 / CBO 优化 / 调度 / Catalog 管理        │
│   物化视图查询重写                              │
└───────────────────────┬──────────────────────┘
                        │
┌───────────────────────▼──────────────────────┐
│            StarRocks BE/CN（向量化执行）       │
│   C++ 全向量化 MPP + SIMD                       │
│   ┌──────────────────────────────────────┐    │
│   │   Data Cache（内存 L1 + NVMe L2）     │    │
│   └──────────────────────────────────────┘    │
└───────────────────────┬──────────────────────┘
                        │ External Catalog（外表，不搬数据）
┌───────────────────────▼──────────────────────┐
│           Iceberg（开放表格式 / 元数据层）     │
│   metadata.json → manifest list → manifest     │
│   snapshot / schema 演进 / 隐藏分区 / 统计     │
│   ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│   │ Parquet  │ │   ORC    │ │ Puffin 统计  │  │
│   │ 数据文件 │ │ 数据文件 │ │ (NDV 等)     │  │
│   └──────────┘ └──────────┘ └──────────────┘  │
└───────────────────────┬──────────────────────┘
                        │
┌───────────────────────▼──────────────────────┐
│              HDFS / S3 / OSS（对象存储）       │
└──────────────────────────────────────────────┘
```

**关键特征**：

- **Iceberg** 是开放的"表格式（table format）"，本身**不是文件格式**——它是数据文件（Parquet/ORC/Avro）之上的一层元数据规范：`metadata.json`（表元数据）→ manifest list（快照清单）→ manifest（文件清单，含每个数据文件的分区值与列级 min/max/null 统计）。它提供 Schema 演进、隐藏分区（Hidden Partitioning）、快照与 Time Travel、ACID 提交、Copy-on-Write / Merge-on-Read 行级更新等表管理能力。
- **StarRocks** 通过 **External Catalog（Iceberg Catalog）** 直接挂载 Iceberg 表，作为"外表"查询湖内数据——元数据通过 REST/Hive/Glue Catalog 获取，数据文件直读对象存储，**不需要把数据导入 StarRocks 内表**。StarRocks 是 C++ 全向量化 MPP 引擎，配合本地 Data Cache（v3.3 默认开启）和异步物化视图（含透明查询重写）实现湖上加速。
- **加速重心**：落在**计算引擎侧**。Iceberg 负责提供精准的元数据/统计以支持文件级裁剪，StarRocks 负责向量化执行、缓存与物化视图加速。

### 2.3 两条技术路线的本质差异

| 视角 | 架构 A：CarbonData + HetuEngine | 架构 B：Iceberg + StarRocks |
|------|------------------------------|---------------------------|
| **设计哲学** | 重存储：把加速能力内建进文件格式 | 重引擎：表格式只管"表的元数据与事务"，加速交给引擎 |
| **格式角色** | 文件格式 + 表语义 + 索引 三合一 | 表格式（元数据层）与文件格式（Parquet/ORC）解耦 |
| **引擎角色** | 联邦虚拟化（JVM，Trino 系） | 极速向量化 MPP（C++，自研内核 + 外表挂载） |
| **耦合度** | 格式与引擎强耦合（CarbonData 主要被 Spark/Hetu 读） | 格式与引擎松耦合（Iceberg 被几乎所有引擎读写） |
| **加速演进** | 受限于 CarbonData 社区活跃度 | 随 StarRocks 引擎版本快速迭代（Data Cache/MV/CBO） |
| **开放性** | 私有格式，生态收窄 | 开放标准，生态最广 |

---

## 三、维度一：存储格式深度对比

### 3.1 CarbonData：列存文件格式 + 重型内建索引

CarbonData 的核心是"一个文件格式同时承担了文件编码、索引、表语义、预聚合"四重职责。

#### 3.1.1 物理布局与多级索引

```
CarbonData 表
  └── Segment（一次加载形成一个 Segment，类似批次/版本单元）
        └── CarbonData File（.carbondata 数据文件）
              └── Blocklet（默认 ≤ 64MB，列存 + Blocklet 级 min/max 索引）
                    └── Column Page（页级编码 + 页级 min/max）
                          └── Column Chunk（按列连续存储）
        └── .carbonindex（Block/Blocklet 级索引文件，独立于数据文件）
```

- **Block / Blocklet 级索引**：B+ 树组织的多级 min/max 索引，谓词查询时可层层裁剪，实际读取量常可下降 1–2 个数量级。
- **粒度优势**：相比 Parquet 仅有 Row Group 级统计、ORC 仅有 Stripe 级统计，CarbonData 的 Blocklet/Page 级索引更细，对高选择性查询更友好。

#### 3.1.2 全局字典编码

- 低基数列（如制式、设备类型、KPI 类型）编码为整型字典，**压缩率约 60%–80%**。
- GROUP BY / 聚合可直接在编码值上执行，避免字符串比较，**延迟物化**（仅在返回结果时解码）。

#### 3.1.3 Sort Columns 与数据局部性

```sql
TBLPROPERTIES ('SORT_COLUMNS'='time_stamp, region_id, cell_id')
```

数据按 Sort Columns 排序落盘，使"时间 + 区域 + 维度"的多维查询天然获得数据聚簇，min/max 裁剪更有效。

#### 3.1.4 二级索引与时空索引（差异化能力）

- **二级索引**：对高基数列（如用户号码 MSISDN）建立辅助索引，支持高效点查，避免全表扫描。
- **时空索引**：基于 GeoHash / GeoSOT 空间填充曲线，把空间相邻的数据在存储上也排布相邻，并原生支持 `IN_POLYGON` 等空间查询。**这是 Iceberg/Hudi/Parquet 截至 2026 年初仍不具备生产可用能力的独占特性。**

#### 3.1.5 内建预聚合（Timeseries / Pre-aggregate DataMap）

```sql
CREATE DATAMAP agg_day ON TABLE network_kpi USING "timeseries"
DMPROPERTIES ('event_time'='collect_time', 'day_granularity'='1')
AS SELECT collect_time, region_id, sum(dl_traffic) FROM network_kpi
   GROUP BY collect_time, region_id;
```

查询时引擎自动路由到最优预聚合（无需改写 SQL），相当于把"指标层/汇聚表"内建进了存储格式。

#### 3.1.6 短板

- **事务/并发能力弱**：缺乏成熟的快照隔离、行级更新、并发写冲突解决；以 Segment 为批次管理，更新/删除（IUD）能力有限，写放大较大。
- **Schema 演进有限**：远不如 Iceberg 灵活，不支持安全的列重命名/重排/类型提升的完整集合。
- **无 Time Travel（快照回溯）等现代表管理能力**。
- **生态收窄**：主要绑定 Spark 与 Presto/Hetu，社区贡献者集中于华为。

### 3.2 Iceberg：表格式（Table Format）+ Parquet/ORC 数据文件

Iceberg 把"表是什么"抽象为一层独立元数据，数据文件本身仍是业界标准的 Parquet/ORC/Avro。

#### 3.2.1 三层元数据结构

```
catalog → 当前 metadata.json 指针
   metadata.json   （表 schema、分区规格、快照历史、属性）
       └── manifest list  （某个 snapshot 的清单列表，含分区范围统计）
             └── manifest file  （数据文件清单：路径 + 分区值 + 列级 min/max/null_count/记录数）
                   └── data file（Parquet / ORC / Avro）
                   └── delete file（位置删除 / 等值删除，MOR）
```

- **文件级裁剪（File Pruning）**：查询可只读 metadata/manifest，依据分区值与列级统计直接跳过不相关的数据文件，无需打开文件本身。
- **大表元数据可扩展**：避免对象存储上昂贵的 LIST 操作，规划阶段从"列目录"变为"读清单"。

#### 3.2.2 隐藏分区（Hidden Partitioning）

通过分区变换（`days(ts)`、`bucket(N, id)`、`truncate`、`year/month/hour` 等）在元数据层维护分区关系，**用户查询时无需显式写分区谓词**，引擎自动做分区裁剪；且分区演进（Partition Evolution）不需要重写历史数据。

#### 3.2.3 Schema 演进与快照 / Time Travel

- **安全的 Schema 演进**：基于列 ID（field-id）而非列名/位置，支持加列、删列、改名、重排、类型提升，历史数据无需重写。
- **快照隔离与 ACID**：每次写入生成新 snapshot，读写隔离；支持 `Time Travel`（按 snapshot-id / 时间戳回溯）与回滚。

#### 3.2.4 行级更新：COW 与 MOR

- **Copy-on-Write**：更新时重写整个数据文件，读快写慢。
- **Merge-on-Read**：写入 delete file（位置/等值删除），读时合并，写快读时需 merge；适合高频更新场景。

#### 3.2.5 统计信息：Puffin

Iceberg 通过 **Puffin** 文件存储表级/列级统计（如 NDV——基于 Theta sketch 的去重计数），供引擎 CBO 生成更优执行计划。

#### 3.2.6 数据文件级编码

数据文件本质是 Parquet/ORC：列存、Row Group/Stripe 级 min/max、字典编码、可选 Bloom Filter、RLE/位打包等。**索引/统计粒度由底层文件格式决定，普遍粗于 CarbonData 的 Blocklet/Page 级索引。**

#### 3.2.7 短板

- **无内建多级细粒度索引/预聚合/时空索引**：裁剪能力主要依赖 manifest 统计 + Parquet/ORC 文件级统计，细粒度弱于 CarbonData；预聚合需引擎侧物化视图实现。
- **小文件与元数据膨胀**：高频写入会产生大量 data/delete/manifest 文件，需要定期 compaction / expire snapshots / rewrite manifests 维护。

### 3.3 存储格式维度对比表

| 能力 | CarbonData | Iceberg（+ Parquet/ORC） |
|------|-----------|--------------------------|
| **本质** | 文件格式 + 索引 + 表语义 三合一 | 表格式（元数据层），数据文件用 Parquet/ORC |
| **列存编码** | 列存 + 全局字典 + 延迟物化 | 由 Parquet/ORC 提供（字典/RLE/位打包） |
| **索引粒度** | Block/Blocklet/Page 多级 min/max（细） | manifest 文件级 + Parquet RowGroup/ORC Stripe 级（较粗） |
| **二级索引** | ✅ 支持（高基数列点查） | ❌ 无原生二级索引（依赖文件统计 + 可选 Bloom Filter） |
| **时空索引** | ✅ GeoHash/GeoSOT + `IN_POLYGON`（生产可用） | ❌ 地理空间仍 WIP（2026 初未 GA） |
| **内建预聚合** | ✅ Timeseries/Pre-agg DataMap（自动路由） | ❌ 无（需引擎侧物化视图） |
| **Schema 演进** | 有限 | ✅ 基于 field-id，加/删/改名/重排/类型提升，历史不重写 |
| **分区** | 静态分区 + Sort Columns | ✅ 隐藏分区 + 分区变换 + 分区演进 |
| **快照 / Time Travel** | ❌ 基本无 | ✅ snapshot 隔离 + Time Travel + 回滚 |
| **ACID / 并发写** | 弱（Segment 批次管理） | ✅ 乐观并发提交，快照隔离 |
| **行级更新** | 有限（IUD，写放大大） | ✅ COW / MOR（等值/位置删除） |
| **统计信息** | 内建多级 min/max | ✅ manifest 列级统计 + Puffin（NDV 等）供 CBO |
| **跨引擎开放性** | 弱（Spark/Hetu 为主） | ✅ 极广（Spark/Flink/Trino/StarRocks/Snowflake/...） |
| **压缩率** | 高（字典 + 列存，60%–80%） | 高（取决于 Parquet/ORC 配置） |
| **适配负载** | 只读 / 多维 OLAP / 时空 | 通用湖仓 / 演进频繁 / 事务更新 / 跨引擎共享 |

**小结**：CarbonData 是"为查询而生的重型存储格式"，把索引和预聚合做进了文件；Iceberg 是"为表管理与开放互操作而生的表格式"，把演进、事务、快照做进了元数据层，而把扫描效率交给 Parquet/ORC + 引擎。

---

## 四、维度二：查询效率深度对比

### 4.1 HetuEngine 查询 CarbonData 的执行链路

```
SQL → HetuEngine Coordinator（解析/优化/分片）
        │  谓词/投影/聚合下推
        ▼
   HetuEngine Worker（JVM，分布式执行）
        │  通过 CarbonData Connector 读取
        ▼
   CarbonData 文件
        │  Block/Blocklet/Page 索引裁剪
        │  字典编码上直接聚合 + 延迟物化
        ▼
   HDFS/OBS/S3
```

**效率特征**：

- **裁剪靠存储格式**：HetuEngine 把谓词推给 CarbonData，由 CarbonData 的多级索引完成数据块裁剪——查询越是命中索引列（Sort/二级/时空），扫描量下降越显著。
- **执行引擎为 JVM 系**：HetuEngine 源自 Trino/Presto，运行在 JVM 上，向量化程度与原生 C++ 引擎有差距；但具备成熟的分布式 pipeline 执行、计算下推、CTE 缓存、元数据缓存。
- **联邦能力是亮点**：可跨源关联（CarbonData ⨝ Hive/HBase/GaussDB），代价是联邦查询的性能上限低于单引擎本地执行。
- **典型增益**：CarbonData 相比原生 Spark SQL 查询提速约 10x（格式贡献）；HetuEngine 跨源下推相比开源方案约 5x（引擎贡献）。

### 4.2 StarRocks 查询 Iceberg 的执行链路

```
SQL → StarRocks FE（解析/CBO 优化/物化视图重写/调度）
        │  基于 Iceberg manifest 统计做文件级裁剪
        │  基于 Puffin/统计做 CBO（join 顺序、分布）
        ▼
   StarRocks BE/CN（C++ 全向量化 MPP + SIMD）
        │  Data Cache（内存 L1 → NVMe L2）命中则本地读
        ▼  miss
   Iceberg 数据文件（Parquet/ORC）
        │  Row Group/Stripe 裁剪 + 列裁剪 + 延迟物化
        ▼
   HDFS/S3/OSS
```

**效率特征**：

- **C++ 全向量化执行**：BE 使用列式内存布局 + SIMD，CPU 效率与交互式延迟普遍优于 JVM 引擎。
- **CBO + 精准统计**：FE 利用 Iceberg manifest 列级统计与 Puffin NDV 做代价优化，生成更优的 join/聚合计划。
- **本地 Data Cache**：把对象存储的远程文件块缓存到本地内存/NVMe，缓存命中时性能接近内表；这是弥补存算分离 IO 短板的核心机制。
- **物化视图查询重写**：异步物化视图可对 Iceberg 表预计算，查询自动重写命中，等价于"引擎侧的预聚合"。
- **外表零导入**：通过 External Catalog 直读 Iceberg，无需 ETL 入库即可分析；冷查询（缓存未命中）受对象存储带宽/延迟限制。
- **典型增益**：行业实践中 StarRocks 查询湖表性能可达 SparkSQL 的 3–8x，资源节省可观。

### 4.3 查询效率维度对比表

| 维度 | 架构 A：HetuEngine + CarbonData | 架构 B：StarRocks + Iceberg |
|------|------------------------------|---------------------------|
| **执行引擎语言/模型** | JVM，Trino/Presto 系 pipeline | C++ 全向量化 MPP + SIMD |
| **向量化程度** | 部分（受 JVM 限制） | 全面向量化 |
| **数据裁剪主力** | CarbonData 多级索引（Blocklet/Page，细） | Iceberg manifest + Parquet/ORC 统计（文件/RowGroup 级，较粗） |
| **CBO 统计来源** | CarbonData 元数据 + Hetu 统计 | Iceberg manifest 列级统计 + Puffin NDV |
| **本地缓存** | 引擎侧 CTE/元数据缓存为主（无强数据块缓存） | Data Cache（内存 + NVMe，v3.3 默认开启，SLRU） |
| **交互式低延迟** | 中 | **高** |
| **高并发点查/聚合** | 中（依赖二级索引） | 高（向量化 + 缓存 + MV 重写） |
| **跨源联邦关联** | **强**（Hetu 原生联邦） | 中（JDBC/多 Catalog，但非主打） |
| **冷查询（缓存未命中）** | 依赖 CarbonData 索引降低扫描量 | 依赖文件裁剪，IO 受对象存储限制 |
| **时空/多维聚合查询** | **强**（格式内建时空索引 + 预聚合） | 中（需物化视图弥补，无时空索引） |
| **典型对比基线** | 约 SparkSQL 的 10x（格式）/ 跨源 5x（引擎） | 约 SparkSQL 的 3–8x（湖上向量化 + 缓存） |

### 4.4 不同查询负载下的效率画像

| 查询负载 | 架构 A 表现 | 架构 B 表现 | 更优 |
|---------|-----------|-----------|------|
| **交互式 BI 仪表盘（亚秒级）** | 中（JVM 延迟、需索引命中） | 高（向量化 + Data Cache + MV） | **B** |
| **多维 OLAP 聚合（time × region × dim）** | 高（Sort + 多级索引 + 预聚合 DataMap） | 高（向量化 + MV，但无内建预聚合） | A≈B（场景定） |
| **时空范围 / 多边形查询** | **高**（GeoHash/GeoSOT 时空索引） | 低—中（无时空索引，靠分区/扫描） | **A** |
| **高基数点查（按用户/ID）** | 中—高（二级索引） | 中（依赖文件统计/Bloom，无二级索引） | **A** |
| **跨源关联（湖 ⨝ 业务库）** | **高**（Hetu 联邦下推） | 中（外部 Catalog/JDBC） | **A** |
| **频繁更新表 / CDC 表分析** | 低（CarbonData IUD 弱） | 高（Iceberg MOR + StarRocks 读合并） | **B** |
| **Schema 频繁演进的表** | 低（演进能力弱） | 高（Iceberg field-id 演进） | **B** |
| **冷数据大表全扫** | 中（索引裁剪有限时退化） | 中（缓存未命中受 IO 限制） | 接近 |

---

## 五、维度三：加速方式深度对比

两种架构的加速哲学根本不同：**架构 A 把加速"沉到存储格式"，架构 B 把加速"沉到计算引擎"。**

### 5.1 架构 A 的加速手段

#### 存储格式侧（CarbonData，主力）

1. **多级索引裁剪**：Block → Blocklet → Page 多级 min/max，谓词查询层层跳过无关数据块。
2. **全局字典编码 + 延迟物化**：低基数列编码为整型，聚合在编码上直接计算，仅最终解码，降低 CPU 与 IO。
3. **Sort Columns 聚簇**：按业务查询模式排序落盘，强化 min/max 裁剪有效性。
4. **二级索引**：高基数列点查加速，避免全扫。
5. **时空索引（GeoHash/GeoSOT）**：把空间相邻数据排布相邻，区域查询从随机 IO 变顺序 IO，`IN_POLYGON` 原生支持。
6. **Timeseries / Pre-aggregate DataMap**：内建多粒度预聚合，查询自动路由到最优汇聚表（SQL 零改造）。

#### 计算引擎侧（HetuEngine，辅助）

7. **计算下推**：谓词/投影/聚合/子查询下推到数据源，减少网络传输并复用源端索引（提速约 5x）。
8. **CTE 缓存**：公用表表达式结果内存缓存，避免重复磁盘读取。
9. **元数据缓存**：缓存 Metastore 元数据，降低规划期延迟。
10. **物化视图**：引擎侧物化加速（能力弱于 StarRocks 的查询重写体系）。

> 特点：加速能力**与格式强绑定**。一旦数据写成 CarbonData，索引与预聚合即"随数据移动"，更换引擎也能复用；但加速天花板受 CarbonData 社区演进速度限制。

### 5.2 架构 B 的加速手段

#### 计算引擎侧（StarRocks，主力）

1. **Data Cache（核心）**：以 1MB Block 为单元，内存 L1 + NVMe L2 两级缓存远程文件块；Cache Key = 文件哈希 + 修改时间 + Block ID；v3.3 默认开启；SLRU（分段 LRU，v3.4+）防止突发冷扫描污染热缓存。
2. **缓存预热（CACHE SELECT）**：主动把目标数据预拉入缓存，适合定时 BI 报表、POC。
3. **自适应缓存填充（v3.3.2+）**：仅为 SELECT 填充、全表扫描不污染缓存、磁盘高负载时自动回退远程读。
4. **一致性哈希 Scan Range 调度**：同一数据块固定路由到同一 BE，最大化缓存命中；增量 Scan Range 部署降低查询启动延迟。
5. **异步物化视图 + 透明查询重写**：对 Iceberg 表预计算，优化器自动重写命中（业务 SQL 零改造），支持分区级增量刷新（Iceberg V1 增量，v3.1.4+），等价于"引擎侧预聚合 + 指标层"。
6. **全向量化执行 + CBO**：SIMD 向量化 + 基于 Iceberg/Puffin 统计的代价优化。

#### 存储格式侧（Iceberg，辅助）

7. **文件级裁剪**：基于 manifest 分区值与列级 min/max/null 统计跳过数据文件，读清单而非 LIST 目录。
8. **隐藏分区裁剪**：分区变换让引擎自动裁剪分区，无需显式分区谓词。
9. **Puffin 统计**：NDV 等列级统计供 CBO。
10. **数据文件级加速**：Parquet/ORC 的 RowGroup/Stripe 裁剪、列裁剪、字典、可选 Bloom Filter。
11. **Compaction / 排序写入**：通过小文件合并、按列排序（含 Z-order/Hilbert 数据聚簇，引擎侧）提升后续扫描裁剪率。

> 特点：加速能力**与引擎强绑定**。Iceberg 只负责提供精准元数据，真正的加速（缓存、物化视图、向量化）随 StarRocks 版本快速迭代——引擎升级即加速升级，且这些加速对任何读 Iceberg 的引擎是通用前提。

### 5.3 加速方式维度对比表

| 加速手段 | 架构 A：CarbonData + HetuEngine | 架构 B：Iceberg + StarRocks |
|---------|------------------------------|---------------------------|
| **加速重心** | 存储格式（索引/字典/预聚合内建） | 计算引擎（缓存/物化视图/向量化） |
| **数据块缓存** | 弱（Hetu 无强本地数据块缓存） | ✅ Data Cache（内存+NVMe，默认开启，SLRU） |
| **缓存预热** | ❌ | ✅ CACHE SELECT |
| **细粒度索引** | ✅ Block/Blocklet/Page 多级 | ❌（文件级统计 + 可选 Bloom） |
| **二级索引** | ✅ | ❌ |
| **时空索引** | ✅ GeoHash/GeoSOT | ❌（WIP） |
| **内建预聚合** | ✅ DataMap（格式自动路由） | ❌（用引擎物化视图替代） |
| **物化视图 + 查询重写** | 一般（Hetu MV） | ✅ 异步 MV + 透明重写 + 分区增量刷新 |
| **字典编码加速聚合** | ✅ 全局字典 + 延迟物化 | 部分（Parquet 字典） |
| **计算/谓词下推** | ✅ Hetu 下推 + CarbonData 索引过滤 | ✅ 谓词/分区/列裁剪下推到文件层 |
| **CBO 统计** | CarbonData 元数据 | ✅ manifest 统计 + Puffin NDV |
| **跨源联邦** | ✅ Hetu 原生 | 中（JDBC/多 Catalog） |
| **加速随版本演进** | 受 CarbonData 社区限制（较慢） | ✅ 随 StarRocks 迭代（快） |
| **加速可移植性** | 高（加速随数据/格式走，跨引擎复用） | 中（核心加速绑定 StarRocks，但 Iceberg 元数据通用） |

### 5.4 关键洞察：两种加速哲学的取舍

- **架构 A（加速在存储）**：一次把索引/预聚合写进格式，任何支持 CarbonData 的引擎都能受益，且对只读/时空/多维场景几乎"开箱即用"。代价是格式重、写入慢、演进受限、社区弱。
- **架构 B（加速在引擎）**：表格式保持轻量开放，加速由引擎承担——更易随引擎升级而持续增强（Data Cache、MV、CBO 持续迭代），且 Iceberg 可被多引擎共享。代价是加速效果依赖具体引擎，换引擎需重建缓存/物化视图。

---

## 六、综合对比矩阵

| 大类 | 子维度 | 架构 A：CarbonData + HetuEngine | 架构 B：Iceberg + StarRocks | 占优 |
|------|--------|------------------------------|---------------------------|------|
| **存储格式** | 形态 | 文件格式 + 索引 + 表语义 三合一 | 表格式 + Parquet/ORC 数据文件 | — |
| | 索引粒度 | 多级（Blocklet/Page），细 | 文件/RowGroup 级，较粗 | A |
| | 时空/二级索引 | ✅ | ❌ | A |
| | 内建预聚合 | ✅ DataMap | ❌（引擎 MV 替代） | A |
| | Schema 演进 | 有限 | ✅ field-id 演进 | B |
| | 事务/快照/Time Travel | ❌/弱 | ✅ ACID + snapshot + 回溯 | B |
| | 行级更新 | 弱（IUD） | ✅ COW/MOR | B |
| | 开放性/跨引擎 | 弱 | ✅ 最广 | B |
| **查询效率** | 执行内核 | JVM（Trino 系） | C++ 全向量化 | B |
| | 交互式低延迟 | 中 | 高 | B |
| | 多维/时空查询 | 高 | 中 | A |
| | 跨源联邦 | 强 | 中 | A |
| | 更新/演进表分析 | 弱 | 高 | B |
| **加速方式** | 加速重心 | 存储格式 | 计算引擎 | — |
| | 数据块缓存 | 弱 | ✅ Data Cache | B |
| | 物化视图重写 | 一般 | ✅ 强 | B |
| | 格式内建加速 | ✅ 强（索引/字典/预聚合） | 一般 | A |
| | 加速演进速度 | 慢（社区弱） | 快（引擎迭代） | B |
| **生态/工程** | 社区活跃度 | 低（华为主导） | 高（开放标准 + Apache 引擎） | B |
| | 厂商锁定风险 | 较高 | 低 | B |
| | 运维复杂度 | 中（格式重，索引/DataMap 维护） | 中（小文件/快照/MV 维护） | 接近 |

---

## 七、选型建议与适用场景

### 7.1 推荐使用架构 A（CarbonData + HetuEngine）的场景

1. **电信网络观测 / 时空分析**：KPI、MR、信令、话单等只读、强时序 + 强空间数据，需 `IN_POLYGON`、网格覆盖分析——CarbonData 时空索引在 1–2 年内仍**无可替代**。
2. **只读 + 多维 OLAP**：Append-only、无 Upsert 需求、以多维聚合为主，格式内建预聚合与多级索引"开箱即用"。
3. **重度跨源联邦分析**：需要把湖数据与 Hive/HBase/GaussDB/关系库做联邦关联，HetuEngine 的联邦下推是核心价值。
4. **既有华为 MRS/FusionInsight 生态**：已有 CarbonData 资产、Spark + Hetu 技术栈，迁移成本低。

### 7.2 推荐使用架构 B（Iceberg + StarRocks）的场景

1. **通用湖仓即席分析 / 实时 BI**：追求亚秒级交互、高并发——StarRocks 向量化 + Data Cache + 物化视图组合效率最高。
2. **需要 Schema 演进 / 事务 / Time Travel 的表**：业务表频繁加列改名、需要快照隔离与回溯、有 CDC/Upsert 需求（Iceberg MOR）。
3. **多引擎共享一份数据**：同一份 Iceberg 表要被 Spark/Flink/Trino/StarRocks 同时读写，避免数据搬运与格式锁定。
4. **规避厂商锁定 / 拥抱开放标准**：Iceberg 已成为海外事实标准，工具与引擎生态最广。
5. **存算分离 + 弹性成本优先**：StarRocks 存算分离 + 对象存储，秒级扩缩容 + 低存储成本。

### 7.3 决策速查

| 你的首要诉求 | 推荐 |
|------------|------|
| 时空 / 网络观测多维分析 | **架构 A** |
| 交互式 BI、高并发即席查询 | **架构 B** |
| 跨源联邦关联 | **架构 A** |
| Schema 演进 / 事务 / Time Travel | **架构 B** |
| 多引擎共享、避免锁定 | **架构 B** |
| 既有华为 CarbonData 资产 | **架构 A** |
| 频繁更新 / CDC 入湖后分析 | **架构 B** |
| 电信运维 XDR（Append-only + 数十亿点查/多维） | **架构 A**（详见第八章） |

---

## 八、电信运维（XDR）场景下的再评估

> 本章在前述"通用结论"之上，专门叠加电信运维类数据的两个限定条件，重新审视存储格式 / 查询效率 / 加速方式三个维度的优劣，并给出该场景下的选型修正。

### 8.1 场景特征：Append-only + 数十亿 XDR 点查/多维查询

电信运维类数据是**电信网络的观测数据**——XDR（eXtended Data Record，含 S1-U/Gn/话单/信令等会话级明细）、MR（测量报告）、KPI 汇聚指标等。其工程特征与通用企业数据存在本质差异：

| 特征 | 电信运维（XDR 观测数据） | 通用企业数据 | 对选型的影响 |
|------|------------------------|-------------|-------------|
| **写入模式** | **Append-only**，数据写入即不可变，无 Update/Delete | 频繁 Upsert/Delete | 开放表格式的事务/行级更新价值被削弱 |
| **数据规模** | 极大，单表**数十亿~万亿行 XDR**，日增 TB 级 | 中—大 | 裁剪/索引能力决定成败 |
| **查询模式 1** | **高基数点查**（按 IMSI/MSISDN/会话 ID/TAC 查指定对象的 XDR 明细） | 多样 | 强依赖二级索引，否则全扫 |
| **查询模式 2** | **多维查询**（时间 × 区域 × 小区 × 网元 × KPI 的过滤聚合） | 多样 | 强依赖多级/排序/（时空）索引 |
| **更新需求** | 无 | 高频 | ACID/MOR/Time Travel 几乎用不上 |
| **Schema 演进** | 弱（XDR 字段相对稳定，扩展以加列为主） | 中—高 | Iceberg 演进优势收窄 |
| **时效/并发** | 准实时入湖 + 中低并发复杂分析（运维/优化工程师） | 多样 | 偏分析吞吐而非超高并发短查询 |

**关键判断**：该场景**绕开了开放表格式（Iceberg）赖以差异化的能力（ACID/行级更新/Time Travel）**，同时**正面命中了 CarbonData 的核心长板（二级索引点查、多级/排序索引多维裁剪、列存高压缩）**。

### 8.2 特征一影响：Append-only 使开放表格式的 ACID 增益有限

Iceberg 在通用场景的核心竞争力，很大一部分来自"表管理与事务"能力。但在 Append-only 的 XDR 场景下，这些能力的边际价值显著下降：

| Iceberg 能力 | 通用场景价值 | 电信运维（Append-only）下的价值 | 说明 |
|-------------|------------|------------------------------|------|
| **ACID 事务提交** | 高（并发读写隔离） | **低** | 仅追加写入，无读写/写写更新冲突，快照隔离的必要性大幅降低 |
| **行级更新（COW/MOR）** | 高 | **几乎为 0** | 数据不可变，不存在 Update/Delete，delete file 机制无用武之地 |
| **Time Travel / 回滚** | 中—高 | **低** | 观测数据以"按时间分区追加"天然具备历史可追溯性，无需 snapshot 回溯纠错 |
| **Schema 演进** | 高 | **低—中** | XDR schema 稳定，偶有加列；CarbonData 的加列能力即可满足 |
| **隐藏分区/分区演进** | 中—高 | **中** | 仍有价值（按天/小时分区），但 CarbonData 的静态分区 + Sort Columns 同样能覆盖 |

**结论**：开放表格式的"事务红利"在 Append-only 观测数据上**大部分无法兑现**。Iceberg 仍保留"开放生态 / 多引擎共享 / 标准化"价值，但其相对 CarbonData 的**功能差异化优势在本场景被大幅抵消**。与此同时，Append-only 反而让 CarbonData 的短板（IUD 弱、并发写冲突处理弱）**不再构成问题**。

> 换言之：在 XDR 场景里，"选 Iceberg 主要为 ACID"这一通用理由基本不成立；选型重心应回归到**存储格式的查询裁剪能力**与**引擎的执行效率**。

### 8.3 特征二影响：数十亿 XDR 点查 / 多维查询的效率分水岭

XDR 的两类核心查询，对两种架构是截然不同的考验。

#### 查询模式 1：数十亿 XDR 高基数点查

典型诉求：在数十亿行中按 `imsi` / `msisdn` / 会话 ID 等**高基数列**定位某对象的全部 XDR 明细。

```sql
-- 查某用户某时间窗内的 XDR 明细
SELECT * FROM xdr WHERE imsi = '460001234567890'
  AND event_time BETWEEN '2026-06-10 00:00:00' AND '2026-06-10 23:59:59';
```

| 架构 | 高基数点查机制 | 数十亿行下的表现 |
|------|--------------|----------------|
| **A：CarbonData + HetuEngine** | **二级索引**直接定位 Blocklet/Block，仅读命中数据块 | **优**：避免全扫，点查可达秒级以内 |
| **B：Iceberg + StarRocks** | 无原生二级索引；依赖分区裁剪 + manifest/Parquet 文件级 min/max + 可选 Bloom Filter | **一般**：若 `imsi` 非分区/排序键，min/max 几乎无裁剪效果，退化为大范围扫描（靠向量化 + Data Cache 缓解，但仍读大量数据） |

> 要点：高基数列的点查是 CarbonData 二级索引的"主场"。Iceberg 的文件级统计对高基数随机值**裁剪能力很弱**（min/max 区间几乎覆盖全域），即使叠加 Bloom Filter 也只能做文件级过滤、粒度粗于 CarbonData 的 Blocklet 级。StarRocks 只能靠 C++ 向量化与缓存把"扫得多但扫得快"做到极致，但数据读取量级上仍处劣势。

#### 查询模式 2：多维过滤聚合查询

典型诉求：按"时间 × 区域 × 小区 × 网元 × KPI"做多维过滤与聚合。

```sql
SELECT cell_id, COUNT(*), AVG(dl_throughput), SUM(drop_count)
FROM xdr
WHERE event_time BETWEEN ... AND region_id = 310115 AND rat = 'NR'
GROUP BY cell_id;
```

| 架构 | 多维查询机制 | 表现 |
|------|------------|------|
| **A：CarbonData + HetuEngine** | Sort Columns 聚簇 + 多级 min/max 裁剪 + 全局字典编码上聚合 + （可选）时空索引 + Timeseries/Pre-agg DataMap 自动路由 | **优**：高选择性多维查询裁剪彻底；常见 KPI 汇聚可命中预聚合，近乎免扫描 |
| **B：Iceberg + StarRocks** | 隐藏分区裁剪 + 文件级 min/max + C++ 全向量化聚合 + Data Cache + 异步物化视图（需预建）透明重写 | **良**：分区/排序键命中时表现好；但无内建预聚合，需为每类汇聚**显式建物化视图并维护刷新**，未命中物化视图时按扫描 + 向量化兜底 |

> 要点：多维查询两者都能做好，但**实现成本不同**。CarbonData 的预聚合是"格式内建、查询自动路由、SQL 零改造"；StarRocks 需要为每种汇聚模式建并维护物化视图（Append-only 下增量刷新友好，是其有利点）。对于 KPI 汇聚模式相对固定的运维报表，两者都能达到目标；对于探索式、维度组合多变的多维下钻，CarbonData 的多级索引更"开箱即用"。

### 8.4 三维度在电信运维场景下的结论修正

| 维度 | 通用结论 | 电信运维（XDR）场景修正 | 修正后倾向 |
|------|---------|----------------------|-----------|
| **存储格式** | B 强在演进/事务/开放；A 强在读优化 | B 的事务/演进红利在 Append-only 下**大幅缩水**；A 的索引/字典/预聚合长板全数命中 | **A 反超** |
| **查询效率** | B 在交互式 OLAP 普遍占优 | 高基数点查 A 凭二级索引明显占优；多维查询 A（内建预聚合）≥ B（需建 MV），仅在超高并发短查询上 B 仍有引擎优势 | **A 占优 / 复杂多维 A≈B** |
| **加速方式** | B 加速在引擎、随版本快速增强 | 本场景所需加速（点查二级索引、多维裁剪、预聚合）多为**格式内建能力**，A 开箱即用；B 需工程化搭建并维护 MV/缓存 | **A 更省工 / B 更灵活** |

**总判断**：在"Append-only + 数十亿 XDR 点查/多维查询"的电信运维限定场景下，**架构 A（CarbonData + HetuEngine）在存储格式与查询效率两个维度反超**，是更契合的技术路线；**架构 B（Iceberg + StarRocks）的价值收敛为"开放生态、多引擎共享、引擎演进速度"**，而非其在通用场景标志性的"事务 + 交互式向量化"。

### 8.5 电信运维场景选型建议

1. **首选架构 A**：若核心诉求是数十亿 XDR 的高基数点查与多维分析、数据 Append-only、且已有华为 MRS/CarbonData 生态——优先 CarbonData + HetuEngine，重点用好**二级索引（点查列）**、**Sort Columns（时间+区域+小区）**、**时空索引（覆盖/网格分析）**、**Timeseries/Pre-agg DataMap（KPI 汇聚）**。
2. **架构 B 作为补充/演进选项**：若强需求是**多引擎共享同一份观测数据**、**规避私有格式锁定**、或希望统一到开放湖仓栈——可选 Iceberg + StarRocks，但需接受为点查/多维做额外工程：合理设计分区与排序写入（按 `event_time`/`region` 排序聚簇）、为高频汇聚建**异步物化视图 + 透明重写**、对高基数点查列开启 Bloom Filter 并依赖 Data Cache。其 ACID 能力在此场景不是主要采购理由。
3. **折中路线**：以 **Iceberg 承载开放存储与多引擎互操作**，对点查/多维**重负载子集**用 StarRocks 物化视图或专用加速层补齐；同时跟踪 Iceberg 二级索引/地理空间能力 GA 进展——一旦补齐，B 在本场景的差距将进一步缩小。
4. **不建议**：在纯 Append-only 的 XDR 场景下，单纯"为 ACID / Time Travel"而选择开放表格式——该红利在此场景兑现不了，反而要承担缺少二级/时空索引带来的点查与多维裁剪损失。

---

## 九、演进趋势研判

1. **开放表格式标准化不可逆**：Iceberg 已被 Databricks、Snowflake、AWS、Spark/Flink/Trino/StarRocks 等广泛支持，正成为湖仓事实标准；CarbonData 作为私有格式将进一步边缘化（但在时空/网络观测的限定场景仍有独占窗口期）。
2. **加速能力持续"上移"到引擎**：Data Cache、物化视图、向量化、CBO 等加速由引擎承担并快速迭代，使"开放轻量表格式 + 强引擎"组合的综合竞争力持续增强。
3. **Iceberg 正在补齐格式侧短板**：地理空间类型（GEOMETRY/GEOGRAPHY + XZ2 分区变换）、Puffin 统计、文件级删除向量等持续演进；一旦 Geospatial GA，CarbonData 时空独占优势将被显著压缩。
4. **联邦与统一引擎融合**：StarRocks 在增强 JDBC/多 Catalog 联邦能力，HetuEngine/Trino 在增强本地执行与缓存；最终形态趋向"强向量化本地引擎 + 轻量联邦扩展"。
5. **建议的长期策略**：新建湖仓优先选择 **Iceberg + 向量化 MPP（如 StarRocks）** 的开放路线；对时空/网络观测等 CarbonData 强项场景，保留 CarbonData 的同时设计存储抽象层，跟踪 Iceberg Geospatial 进展以便平滑迁移。

---

## 附录：参考来源索引

> 说明：本文在技术机制层面综合了同目录《华为 GaussDB/CarbonData 湖仓一体架构深度调研与对比分析》中的调研结论，并结合 Apache CarbonData、Apache Iceberg、StarRocks、HetuEngine 的公开官方文档进行对比展开。

| 编号 | 主题 | 参考 |
|------|------|------|
| [R1] | Apache CarbonData 文件格式与索引/DataMap | https://carbondata.apache.org/ |
| [R2] | CarbonData 时空索引 / IN_POLYGON | https://carbondata.apache.org/ （Spatial Index 文档） |
| [R3] | Apache Iceberg 表格式规范（metadata/manifest/snapshot） | https://iceberg.apache.org/spec/ |
| [R4] | Iceberg 隐藏分区与分区演进 | https://iceberg.apache.org/docs/latest/partitioning/ |
| [R5] | Iceberg Puffin 统计文件格式 | https://iceberg.apache.org/puffin-spec/ |
| [R6] | StarRocks External Catalog（Iceberg Catalog） | https://docs.starrocks.io/docs/data_source/catalog/iceberg_catalog/ |
| [R7] | StarRocks Data Cache | https://docs.starrocks.io/docs/data_source/data_cache/ |
| [R8] | StarRocks 物化视图与查询重写 | https://docs.starrocks.io/docs/using_starrocks/async_mv/Materialized_view/ |
| [R9] | HetuEngine 联邦查询与计算下推 | 华为云 MRS HetuEngine 官方文档 |
| [R10] | 同目录调研报告 | `./华为GaussDB-CarbonData湖仓一体深度调研与对比分析.md` |
