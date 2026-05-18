# 华为 GaussDB/CarbonData 湖仓一体架构深度调研与对比分析

> **调研范围**：华为云 GaussDB(DWS)、HetuEngine、CarbonData、LakeFormation；StarRocks 3.x/4.x；LakeSoul 3.0  
> **更新日期**：2026年5月  
> **核心问题**：华为 GaussDB 是否直接查询湖数据？存算分离下 MPP 性能的 Trade-off 机制是什么？与 StarRocks、LakeSoul 的湖仓方案有何本质差异？

---

## 目录

- [一、核心结论摘要](#一核心结论摘要)
- [二、华为湖仓一体架构深度剖析](#二华为湖仓一体架构深度剖析)
  - [2.1 架构全景：从 MRS 到 GaussDB(DWS) 的双轨融合](#21-架构全景从-mrs-到-gaussdbdws-的双轨融合)
  - [2.2 GaussDB(DWS) 3.0 存算分离架构](#22-gaussdbdws-30-存算分离架构)
  - [2.3 CarbonData 在华为生态中的定位与演变](#23-carbondata-在华为生态中的定位与演变)
  - [2.4 HetuEngine：联邦查询与数据虚拟化引擎](#24-hetuengine联邦查询与数据虚拟化引擎)
  - [2.5 LakeFormation：统一元数据与权限中枢](#25-lakeformation统一元数据与权限中枢)
  - [2.6 核心猜测验证：GaussDB 是否直接查询湖数据？](#26-核心猜测验证gaussdb-是否直接查询湖数据)
- [三、存算分离下 MPP 性能 Trade-off 深度分析](#三存算分离下-mpp-性能-trade-off-深度分析)
  - [3.1 存算分离的根本矛盾](#31-存算分离的根本矛盾)
  - [3.2 华为 GaussDB(DWS) 的五层缓解机制](#32-华为-gaussdbdws-的五层缓解机制)
  - [3.3 性能损失的量化评估](#33-性能损失的量化评估)
  - [3.4 华为做出的关键 Trade-off 决策](#34-华为做出的关键-trade-off-决策)
- [四、StarRocks 湖仓一体机制深度分析](#四starrocks-湖仓一体机制深度分析)
  - [4.1 架构概述：MPP + External Catalog](#41-架构概述mpp--external-catalog)
  - [4.2 Data Cache：核心性能保障机制](#42-data-cache核心性能保障机制)
  - [4.3 物化视图加速湖上查询](#43-物化视图加速湖上查询)
  - [4.4 存算分离 vs 存算一体的功能与性能差异](#44-存算分离-vs-存算一体的功能与性能差异)
- [五、LakeSoul 湖仓一体机制深度分析](#五lakesoul-湖仓一体机制深度分析)
  - [5.1 架构概述：云原生实时湖仓框架](#51-架构概述云原生实时湖仓框架)
  - [5.2 NativeIO：Rust 向量化读写引擎](#52-nativeiorust-向量化读写引擎)
  - [5.3 Merge on Read 与 Upsert 机制](#53-merge-on-read-与-upsert-机制)
  - [5.4 与 MPP 引擎的集成方案](#54-与-mpp-引擎的集成方案)
- [六、三者深度对比分析](#六三者深度对比分析)
  - [6.1 架构定位对比](#61-架构定位对比)
  - [6.2 存算分离性能补偿机制对比](#62-存算分离性能补偿机制对比)
  - [6.3 湖上查询加速机制对比](#63-湖上查询加速机制对比)
  - [6.4 适用场景与 Trade-off 对比](#64-适用场景与-trade-off-对比)
- [七、行业演进趋势与研判](#七行业演进趋势与研判)
  - [7.1 存算分离成为不可逆趋势](#71-存算分离成为不可逆趋势)
  - [7.2 开放表格式标准化竞争](#72-开放表格式标准化竞争)
  - [7.3 统一引擎与联邦查询的博弈](#73-统一引擎与联邦查询的博弈)
  - [7.4 华为方案的演进预判](#74-华为方案的演进预判)
- [八、限定场景再评估：SmartCare 网络观测数据下的 CarbonData](#八限定场景再评估smartcare-网络观测数据下的-carbondata)
  - [8.1 场景特征分析：网络观测数据的独特性](#81-场景特征分析网络观测数据的独特性)
  - [8.2 CarbonData 在该限定场景下的优势重估](#82-carbondata-在该限定场景下的优势重估)
  - [8.3 CarbonData 时空索引：电信网络的"杀手级特性"](#83-carbondata-时空索引电信网络的杀手级特性)
  - [8.4 预聚合与时间序列 DataMap：内建 KPI 汇聚能力](#84-预聚合与时间序列-datamap内建-kpi-汇聚能力)
  - [8.5 限定场景下与 Hudi/Iceberg/Parquet 的对比逆转](#85-限定场景下与-hudiicebergparquet-的对比逆转)
  - [8.6 修正后的结论](#86-修正后的结论)
- [九、给技术决策者的建议](#九给技术决策者的建议)
- [附录：参考来源索引](#附录参考来源索引)

---

## 一、核心结论摘要

经过深入调研，对提出的核心猜测做出如下验证与扩展：

### 猜测验证

| 猜测 | 验证结论 | 置信度 |
|------|---------|--------|
| GaussDB 不单独增加硬件，与数据湖统一配置 | **确认**。GaussDB(DWS) 3.0 采用存算分离架构，数据统一存储在 OBS，通过 Virtual Warehouse (VW) 共享数据，无需独立硬件 | 高 |
| GaussDB 直接查询湖数据 | **确认，但机制比猜测更复杂**。GaussDB 通过外表 (Foreign Table) 直接查询 OBS 上的 Hudi/Parquet/ORC/CarbonData 数据；同时提供自动增量同步机制将热数据物化到内表 | 高 |
| 存算不一体导致性能差距 | **确认**。华为通过"五层缓解机制"（本地缓存、近数据计算、IO 调度、智能物化、索引过滤）来弥补，但冷查询性能仍有 2-5x 差距 | 高 |
| 必然存在 Trade-off | **确认**。核心 Trade-off 是"弹性成本 vs 极致性能"，华为选择了偏向弹性与成本的路线，通过多层缓存和智能调度尽量缩小性能差距 | 高 |

### 超出原始思考的关键发现

1. **华为实际上构建了三层查询路径**：直接外表查询（最灵活但最慢）→ HetuEngine 联邦查询（中间层，带计算下推）→ 内表同步（最快但最重）；这三层可根据数据温度和业务 SLA 灵活组合
2. **CarbonData 角色需要分场景判断**（详见第八章修正分析）：在通用湖仓一体场景中确实被 Hudi/Iceberg 分流；但在 **SmartCare 网络观测数据**这类"只读 + 多维分析 + 时空查询"的限定场景下，CarbonData 的时空索引、预聚合、多级索引体系仍具有 **1-2 年内无可替代的独占优势**
3. **HetuEngine 是华为湖仓一体的"隐藏关键组件"**，它实际上充当了湖仓之间的数据虚拟化层，通过查询下推将性能提升 5x，远非简单的"GaussDB 直接读 OBS"

---

## 二、华为湖仓一体架构深度剖析

### 2.1 架构全景：从 MRS 到 GaussDB(DWS) 的双轨融合

华为的湖仓一体方案并非单一产品，而是由多个组件协同构成的完整体系：

```
┌─────────────────────────────────────────────────────────┐
│                     应用/分析层                          │
│         BI 工具 / 数据科学平台 / 业务应用                 │
└───────────┬─────────────────────────────┬───────────────┘
            │                             │
┌───────────▼───────────┐   ┌─────────────▼───────────────┐
│   GaussDB(DWS) 3.0   │   │    HetuEngine (联邦查询)     │
│   MPP 分析引擎        │   │    数据虚拟化引擎            │
│   - Virtual Warehouse │   │    - 计算下推               │
│   - 列存/行存引擎     │   │    - 跨源协同分析            │
│   - 外表查询能力      │   │    - CTE 缓存               │
└───────────┬───────────┘   └─────────────┬───────────────┘
            │                             │
┌───────────▼─────────────────────────────▼───────────────┐
│              LakeFormation (统一元数据)                   │
│     统一 Catalog / 细粒度权限 / 跨引擎数据共享            │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│              OBS (对象存储 - 统一存储层)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │ Hudi     │ │ Parquet  │ │  ORC     │ │ CarbonData │  │
│  │ COW/MOR  │ │          │ │          │ │  (历史)    │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
│  │ Iceberg  │ │ CSV/TEXT │ │ JSON     │                 │
│  └──────────┘ └──────────┘ └──────────┘                 │
└─────────────────────────────────────────────────────────┘
```

**核心设计理念**：所有数据统一存储在 OBS 上（开放格式 + 私有格式），通过 LakeFormation 统一元数据管理，GaussDB(DWS) 和 HetuEngine 作为两种互补的计算引擎层，根据场景选择最优查询路径。

### 2.2 GaussDB(DWS) 3.0 存算分离架构

GaussDB(DWS) 历经 12 年技术演进（2011年预研 → 2014年首发 → 2023年推出 3.0 云原生版本），架构从 Shared-Nothing MPP 演变为**存算管三层分离**：

#### 三层分离详解

| 层 | 职责 | 关键组件 |
|----|------|---------|
| **管理层** | 查询优化、权限管理、全局事务、元数据管理 | Coordinator Node (CN)、LakeFormation |
| **计算层** | SQL 执行、数据处理 | Virtual Warehouse (VW)，每 VW 包含若干 DN，最多 256 个 VW |
| **存储层** | 数据持久化 | OBS（开放格式）+ EVS（热数据缓存/行存/索引） |

#### Virtual Warehouse (VW) 机制

VW 是 GaussDB(DWS) 3.0 的核心创新：

- **定义**：逻辑集群，一组可灵活添加或释放的计算单元
- **数据关系**：数据不属于任何 VW，VW 与数据仅为"绑定关系"
- **弹性能力**：计算节点扩容无需数据重分布，支持不中断业务的弹性伸缩
- **隔离性**：不同业务绑定不同 VW，实现负载隔离
- **规模上限**：单集群最多 2,048 DN，单 VW 最多 1,024 DN，推荐单 VW ≤ 128 DN

#### 表存储模型

GaussDB(DWS) 3.0 支持三种表存储模型，体现了明确的性能-成本 Trade-off：

| 存储模型 | 存储介质 | 适用场景 | 性能特征 |
|---------|---------|---------|---------|
| **列存表 3.0** | OBS | 批量入库、大规模查询、低频更新 | IO 成本较高，依赖缓存加速 |
| **列存表 2.0** | 本地 EVS | 高频查询、性能敏感场景 | 性能最优，但存储成本高 |
| **行存表** | 本地 EVS | 点查、实时更新、高并发 OLTP | 适合小数据量随机访问 |

### 2.3 CarbonData 在华为生态中的定位与演变

**历史角色**：CarbonData 是华为贡献给 Apache 基金会的列式存储格式，集成于 Spark 生态，曾是 FusionInsight MRS 的核心组件。其核心优势包括：

- 查询速度约为原生 Spark SQL 的 10x
- 多级索引结构（Block/Blocklet 级），支持细粒度扫描
- 全局字典编码与延迟物化
- 数据压缩率 60%-80%

**当前地位（2025-2026）**：

CarbonData 在华为生态中的角色正在**显著弱化**，表现为：

1. **GaussDB(DWS) 湖仓融合的核心格式已转向 Hudi**：DWS 的自动增量同步、CDC 入湖、元数据打通等高级功能都基于 Hudi 构建，CarbonData 仅作为外表查询支持的格式之一
2. **MRS 中的维护状态**：CarbonData 在 MRS 3.x 中仍保留组件支持，但新功能开发已明显放缓
3. **行业生态弱势**：Hudi、Iceberg、Paimon 已形成开放表格式的三足鼎立格局，CarbonData 因缺乏社区推力而边缘化

**根因分析**：CarbonData 定位为"列存文件格式 + 索引"，缺乏 Hudi/Iceberg 那样的事务管理、Schema 演进、Time Travel 等现代湖仓必备能力，在湖仓一体的范式转移中竞争力不足。

### 2.4 HetuEngine：联邦查询与数据虚拟化引擎

HetuEngine 是理解华为湖仓一体方案的关键——它解释了"GaussDB 不单独增加硬件"的深层原因：

#### 核心能力

| 能力 | 说明 |
|------|------|
| **跨源协同分析** | 通过标准 SQL 统一查询 GaussDB、Hive、HBase、ClickHouse、MySQL、Oracle 等 |
| **计算下推** | 将谓词、投影、子查询、聚合等操作推送到数据源执行，性能提升 5x |
| **动态数据源管理** | 添加/删除数据源无需重启，减少 95% 运维负担 |
| **CTE 缓存** | 公用表表达式内存缓存，避免多次磁盘读取 |
| **元数据缓存** | 缓存 Hive Metastore 元数据，减少元数据访问延迟 |
| **弹性伸缩** | 支持横向扩展多计算实例，无损业务动态部署 |

#### 计算下推机制详解

HetuEngine 的计算下推是分层的：

```
           HetuEngine 查询优化器
                    │
        ┌───────────┼───────────┐
        │           │           │
  谓词下推     聚合下推     子查询下推
  (WHERE)    (GROUP BY)    (子SELECT)
        │           │           │
        └───────────┼───────────┘
                    │
              数据源执行
         (GaussDB / Hive / ...)
```

下推的效果不仅是减少网络传输，更关键的是**让数据源利用自身的索引和执行引擎优势**。例如下推到 GaussDB 时可利用其 MPP 并行能力和列存索引，下推到 HBase 时可利用其行键索引。

#### 实际性能数据

- 中国工商银行案例：交互查询响应时间从 1000s 降至 20s，**提效 50x**
- 跨源协同分析相比开源方案：**加速 5x**
- 亿级数据支持秒级跨域查询

### 2.5 LakeFormation：统一元数据与权限中枢

LakeFormation 是华为解决"湖仓数据孤岛"问题的核心服务：

#### 解决的核心问题

在传统的"湖 + 仓"两层架构中，湖和仓各自维护独立的元数据。即使数据存储在同一个 OBS 上，不同引擎也无法直接共享——仍需 ETL 搬运。LakeFormation 通过统一元数据打破这一壁垒。

#### 关键功能

- **统一 Catalog**：兼容 Hive Metastore 元数据模型，所有引擎（MRS、DWS、DLI）通过同一 Catalog 发现和访问数据
- **细粒度权限**：库/表/列级访问控制，兼容 Ranger 权限模型，一次授权全局生效
- **跨集群共享**：MRS 集群 A 创建的表，MRS 集群 B 和 DWS 集群均可直接查询，无需数据拷贝
- **OBS 路径联动**：元数据权限与 OBS 对象存储路径的读写权限自动联动

### 2.6 核心猜测验证：GaussDB 是否直接查询湖数据？

**结论：是的，但远非"简单直查"那么简单。** 华为实际构建了三条分级查询路径：

#### 路径一：外表直查（Direct Foreign Table Query）

```sql
-- GaussDB 通过外表直接查询 OBS 上的 Hudi 数据
CREATE FOREIGN TABLE hudi_table (...)
  SERVER obs_server
  OPTIONS (format 'hudi', foldername '/obs-bucket/hudi/table/');

SELECT * FROM hudi_table WHERE dt = '2024-01-01';
```

- **实现机制**：GaussDB 创建指向 OBS 的外表，直接发起远程 IO 读取
- **性能特征**：受限于网络延迟和 OBS 带宽，适合小数据量或低频查询
- **支持格式**：Hudi（COW/MOR）、Parquet、ORC、CarbonData、Iceberg、CSV/JSON

#### 路径二：HetuEngine 联邦查询（Federated Query with Pushdown）

```
应用层 → HetuEngine → 计算下推 → GaussDB/Hive/HBase
                                    ↓
                               各数据源本地执行
```

- **实现机制**：HetuEngine 作为统一入口，智能判断查询下推策略
- **性能特征**：相比路径一提升 5x，利用了各数据源的本地执行优势
- **适用场景**：跨源关联查询、复杂分析场景

#### 路径三：智能物化同步（Intelligent Materialization Sync）

```sql
-- 创建 Hudi 自动同步任务，增量同步到 GaussDB 内表
SELECT pg_catalog.create_hudi_sync_table();
SELECT hudi_set_sync_commit('schema.inner_table', 'schema.foreign_table', 'latest_commit');
SELECT hudi_sync_task_submit('schema.inner_table', 'schema.foreign_table');
```

- **实现机制**：定期将 Hudi 外表的增量数据合并到 GaussDB 内表
- **性能特征**：查询性能等同于本地 MPP 表，代价是需要维护同步任务
- **适用场景**：高频查询、SLA 要求严格的业务表

#### 三条路径的 Trade-off 矩阵

| 维度 | 路径一：外表直查 | 路径二：联邦查询 | 路径三：物化同步 |
|------|----------------|----------------|----------------|
| **查询延迟** | 高（秒~分钟级） | 中（亚秒~秒级） | 低（毫秒~亚秒级） |
| **数据时效性** | 实时 | 实时 | 近实时（取决于同步频率） |
| **存储成本** | 零额外成本 | 零额外成本 | 需要额外内表存储 |
| **运维复杂度** | 低 | 中 | 高（需管理同步任务） |
| **适用数据温度** | 冷数据 | 温数据 | 热数据 |

---

## 三、存算分离下 MPP 性能 Trade-off 深度分析

### 3.1 存算分离的根本矛盾

传统 MPP 架构（如 GaussDB DWS 2.0、Greenplum）遵循"数据亲和性"原则——数据与计算紧密绑定在同一节点，本地 SSD 的随机读延迟在 **0.1ms** 级别。存算分离后，数据从本地 SSD 迁移到对象存储（OBS/S3），带来两个根本性变化：

| 指标 | 本地 SSD | 对象存储 (OBS/S3) | 差距倍数 |
|------|---------|------------------|---------|
| 随机读延迟 | 0.1ms | 10-100ms | 100-1000x |
| 顺序读带宽（单节点） | 3-6 GB/s (NVMe) | 0.1-1 GB/s | 3-60x |
| IOPS | 100K+ | 1K-10K（受 API 限制） | 10-100x |

这种 IO 特性的巨大差异意味着：**直接将 MPP 的执行模式搬到存算分离架构上，性能将发生数量级退化。** 这正是你观察到的"GaussDB 不单独增加硬件"但"必然存在性能差距"的根本原因。

### 3.2 华为 GaussDB(DWS) 的五层缓解机制

华为通过五层机制来弥合存算分离带来的性能差距：

#### 第一层：本地 EVS 磁盘缓存

```
热数据 → 本地 EVS 磁盘缓存 → 接近本地表性能
冷数据 → OBS 远程读取 → 性能受限于网络
```

- **缓存对象**：OBS 上的列存数据块
- **缓存容量建议**：OBS 总数据量的 30%（初始参考值）
- **磁盘配置**：
  - 性能优先：每 DN 主备各挂 500GB EVS（带宽 350MB/s）
  - 成本优先：每 DN 主备各挂 200GB EVS（带宽 160MB/s）
- **缓存命中时**：性能与本地表相同
- **淘汰策略**：LRU，基于数据块访问频率

#### 第二层：近数据计算（Compute-Near-Data）

将计算逻辑推送到存储层执行，减少需要通过网络传输的数据量：

```
传统模式：OBS → 网络传输全量数据 → 计算节点过滤/聚合
近数据计算：OBS → 存储层执行过滤/聚合 → 网络传输结果集
```

通过分区裁剪、列裁剪、谓词下推等手段，实际需要传输的数据量可降低 90% 以上。

#### 第三层：多层索引过滤

```
查询条件 → 分区裁剪 (Partition Column)
         → 哈希定位 (Distribute Column) 
         → Min-Max 索引 (CU 粗过滤)
         → Bitmap 索引 (行级精确定位)
```

每一层索引都在减少实际需要读取的数据量。对于选择性好的查询，可将 IO 量降低 2-3 个数量级。

#### 第四层：IO 调度优化

- **带宽利用**：充分利用云存储的聚合带宽（OBS 的聚合读带宽远高于单节点）
- **单查询加速**：通过并发 IO 请求最大化利用 OBS 带宽
- **并发查询隔离**：为每个查询提供稳定、可预测的 IO 资源

#### 第五层：冷热数据自动分层

```
热数据（频繁访问）      → 本地 EVS → 高性能
温数据（偶尔访问）      → OBS + 缓存 → 中等性能
冷数据（极少访问）      → OBS 归档 → 低性能但低成本
```

支持两种自动迁移策略：
- **LMT（Last Modified Time）**：按最后修改时间判断冷热
- **HPN（Hot Partition Number）**：保留最近 N 个分区为热数据

### 3.3 性能损失的量化评估

基于调研数据，存算分离的性能损失可用以下模型描述：

| 查询场景 | 缓存命中 | 缓存未命中 | 性能差距 (vs 本地 MPP) |
|---------|---------|-----------|---------------------|
| 热数据点查 | ✓ | — | ≈1x（无差距） |
| 热数据扫描分析 | ✓ | — | 1-1.2x |
| 温数据分析（部分命中） | 部分 | 部分 | 1.5-3x |
| 冷数据全表扫描 | — | ✓ | 3-10x |
| 跨温冷数据关联查询 | 部分 | 部分 | 2-5x |

**关键洞察**：性能损失不是线性的，而是高度依赖缓存命中率。华为的策略是通过智能缓存管理，让 80% 的查询（二八原则）命中本地缓存，从而在整体 QoS 上做到"几乎无感"的存算分离。

### 3.4 华为做出的关键 Trade-off 决策

#### Trade-off 1：弹性 vs 性能

**选择**：优先弹性，通过缓存弥补性能。

**收益**：
- 计算节点扩容无需数据重分布（传统 MPP 扩容需要数小时~天级别的数据 Rebalance）
- 按需调整 VW 数量和规模
- 存储容量理论无限（OBS）

**代价**：
- 冷查询性能显著低于本地 MPP
- 需要合理配置 EVS 缓存容量

#### Trade-off 2：数据时效性 vs 查询性能

**选择**：通过三条查询路径（外表直查/联邦查询/物化同步），将决策权交给用户。

**隐含假设**：大部分企业场景可以容忍"分钟级延迟"的准实时分析，不需要所有数据都达到毫秒级查询响应。

#### Trade-off 3：统一存储 vs 私有格式性能

**选择**：同时支持开放格式（OBS 上的 Hudi/Parquet）和私有格式，但私有格式性能更优。

**矛盾点**：开放格式实现了湖仓数据共享，但 GaussDB 的私有列存格式（带有专有索引和编码）性能更好。用户需要在"数据共享便利性"和"查询性能"之间做出选择。

#### Trade-off 4：运维简单性 vs 极致性能

**选择**：通过 LakeFormation 和 HetuEngine 简化运维，代价是引入了额外的组件复杂性。

GaussDB + HetuEngine + LakeFormation 的组合相比单一 MPP 引擎在运维上增加了系统复杂度，但换来了跨源分析和统一管理的能力。

---

## 四、StarRocks 湖仓一体机制深度分析

### 4.1 架构概述：MPP + External Catalog

StarRocks 的湖仓一体采用了与华为截然不同的路径——**以 MPP 查询引擎为核心，向外扩展数据源接入能力**：

```
┌─────────────────────────────────────────────┐
│            StarRocks FE (前端)               │
│     查询解析 / 优化 / 调度 / Catalog 管理     │
└───────────────────┬─────────────────────────┘
                    │
        ┌───────────┼───────────────┐
        │                           │
┌───────▼───────┐         ┌────────▼────────┐
│ Internal Table │         │ External Catalog │
│ (BE 本地存储)  │         │ (Hive/Iceberg/  │
│               │         │  Hudi/Paimon/   │
│               │         │  Delta Lake)     │
└───────────────┘         └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │   Data Cache    │
                          │ (本地 NVMe 缓存) │
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │ Remote Storage  │
                          │ (HDFS/S3/OSS)   │
                          └─────────────────┘
```

#### 核心特点

- **统一 Catalog 管理**：Unified Catalog 支持同时访问 Hive、Iceberg、Hudi、Paimon 等多种数据源
- **MPP 向量化引擎**：C++ 实现的全面向量化执行引擎，利用 SIMD 指令集加速
- **两种部署模式**：存算一体（Shared-Nothing）和存算分离（Shared-Data），但**不支持混合部署或模式转换**

### 4.2 Data Cache：核心性能保障机制

Data Cache 是 StarRocks 湖仓一体性能的命脉，从 v2.5 开始提供，v3.3.0 起默认开启。

#### 缓存架构

```
查询请求 → 内存缓存 (L1) → 磁盘缓存 (L2, NVMe) → 远程存储 (S3/HDFS)
              ↓ miss           ↓ miss               ↓
           磁盘读取          远程拉取             直接读取
```

- **缓存单元**：以 1MB 数据块 (Block) 为最小缓存单元
- **Cache Key**：文件哈希 + 文件修改时间 + Block ID 组成全局唯一标识
- **缓存介质**：支持内存 + 磁盘两级缓存

#### 淘汰策略

- **LRU**：经典最近最少使用策略
- **SLRU（Segmented LRU，v3.4+）**：分为"淘汰段"和"保护段"，高频访问数据进入保护段后不易被突发冷数据冲走

#### 智能缓存填充（v3.3.2+）

```
自适应模式 (auto)：
  - 仅为 SELECT 查询填充缓存
  - 全分区全列扫描不填充（避免全表扫描污染缓存）
  - 磁盘 IO 负载高时自动路由到远程存储
  - 统计信息收集 SQL 不填充缓存
```

#### 缓存预热（Cache Warmup）

```sql
-- 主动预热指定数据到缓存
CACHE SELECT col1, col2 FROM catalog.db.table WHERE dt = '2024-01-01';
```

适用于 POC 性能测试、定时 BI 报表等具有稳定访问模式的场景。

#### Scan Range 调度优化

- **一致性哈希分配**：同一数据块始终路由到同一 BE 节点，最大化缓存命中率
- **增量 Scan Range 部署（v3.3+）**：FE 在扫描完所有文件前即可开始在 BE 执行，降低查询启动延迟

### 4.3 物化视图加速湖上查询

StarRocks 从 v3.1 开始支持基于 External Catalog 的异步物化视图，这是与 GaussDB 的"Hudi 自动同步"类似的机制：

#### 支持矩阵

| Catalog 类型 | 增量刷新 | 查询重写 |
|-------------|---------|---------|
| Hive | 支持（分区级） | 支持 |
| Iceberg (V1) | 支持（v3.1.4+） | 支持 |
| Paimon | 支持（分区级） | 支持 |
| Hudi | 仅全量刷新 | 支持 |

#### 核心能力

1. **透明查询重写**：创建物化视图后，优化器自动将匹配的查询重写为物化视图访问，业务 SQL 零改造
2. **增量刷新**：仅刷新变更分区，降低计算和 IO 成本
3. **指标层构建**：通过预聚合物化视图构建轻量级指标层

相比纯 Data Cache，物化视图还能利用 StarRocks 的本地索引、分区和分桶能力进一步加速。

### 4.4 存算分离 vs 存算一体的功能与性能差异

StarRocks 的两种模式有明确的功能差异：

| 功能 | 存算一体（Shared-Nothing） | 存算分离（Shared-Data） |
|------|-------------------------|----------------------|
| 主键表 | 支持（v1.x+） | 支持（v3.1+） |
| 列模式部分更新 | 支持（v3.1） | 待支持 |
| 行列混存 | 支持（v3.2+） | 待支持 |
| 向量索引 | 支持（v3.4+） | 待支持 |
| 备份与恢复 | 支持 | 不适用 |
| 跨节点 Data Cache 共享 | 不适用 | 支持（v3.5.1+） |
| 弹性扩缩容 | 需数据 Rebalance | 秒级 |

**性能特征**：
- 缓存命中时：存算分离 ≈ 存算一体
- 冷查询：存算分离约为存算一体的 30-50%
- 行业实践（白山云案例）：StarRocks 查询 Hudi 性能为 SparkSQL 的 3-8x，资源节省 70%

---

## 五、LakeSoul 湖仓一体机制深度分析

### 5.1 架构概述：云原生实时湖仓框架

LakeSoul 的定位与 GaussDB 和 StarRocks 有本质区别——它是**存储框架**而非查询引擎，类似于 Hudi/Iceberg 的角色，但有更强的实时和云原生特性：

```
┌─────────────────────────────────────────────────────────┐
│                    计算引擎对接层                         │
│  Spark / Flink / Presto+Velox / PyTorch / Pandas / Ray  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   Arrow Flight SQL RPC                   │
│              高性能列式数据读写网关服务                     │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                 NativeIO (Rust 实现)                      │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│    │ 向量化 Parquet │  │ Merge on Read│  │ 本地热数据   │  │
│    │ 读写引擎      │  │ 多文件合并    │  │ 缓存        │  │
│    └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              元数据管理层 (PostgreSQL)                     │
│       MVCC / 两阶段提交 / 自动冲突解决 / ACID 事务         │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                  对象存储 (S3/OSS/HDFS)                   │
│              Parquet 文件 (base + delta)                  │
└─────────────────────────────────────────────────────────┘
```

### 5.2 NativeIO：Rust 向量化读写引擎

NativeIO 是 LakeSoul 的核心差异化技术，使用 Rust 语言实现：

#### 技术架构

- **底层库**：基于 Apache Arrow 和 arrow-rs（Rust 原生 Arrow 实现）
- **跨语言支持**：通过 CFFI 接口提供给 Java、Python 等语言调用
- **向量化处理**：利用 Arrow 的列式内存布局和 SIMD 加速

#### 性能优化（3.0.0 版本）

- 调整写入文件压缩和字典编码算法
- 优化 Merge on Read 关键代码路径
- 读写性能相比 2.6 版本**提升一倍**
- 新增本地热数据缓存功能

#### 分区过滤优化

通过元数据索引查询方式，单表百万级分区的分区过滤仅需 **50ms**——这对于大规模数据湖场景是关键优化。

### 5.3 Merge on Read 与 Upsert 机制

LakeSoul 采用单层类 LSM-Tree 方式实现 Upsert：

```
写入流程：
  新数据 → 按主键哈希分片 → 排序 → 写入 Delta File (Parquet)

读取流程：
  Base File + Delta File 1 + Delta File 2 + ...
              ↓
  NativeIO 多文件有序合并 (Merge on Read)
              ↓
  最新版本数据
```

支持 Range 和 Hash 两种分区方式，支持行级和列级的增删改操作。

#### Compaction 策略（3.0.0 版本）

新一代**分层 Size-tiered 自动后台 Compaction 服务**：
- 性能显著提升并大幅减少写放大
- 支持全局合并（集群中启动一次即可对所有表自动合并）
- 分离式合并服务，与主计算流水线独立
- 通过 Spark Dynamic Allocation 实现弹性伸缩

### 5.4 与 MPP 引擎的集成方案

LakeSoul 本身不包含 MPP 查询引擎，而是通过多种方式与外部引擎集成：

| 引擎 | 集成方式 | 向量化支持 | 特色 |
|------|---------|-----------|------|
| **Presto + Velox** | Presto Connector | 原生向量化 | 高性能 MPP 湖上分析 |
| **Spark + Gluten** | Catalog + DataSource | 原生向量化 | 批计算性能大幅提升 |
| **Apache Doris** | 深度集成 | Doris 原生 | CDC 流同步、自动 Schema 演变 |
| **Flink** | Table API + SQL | — | 流批一体读写，Changelog 语义 |
| **PyTorch / Ray** | Python API | — | AI 训练数据读取 |

---

## 六、三者深度对比分析

### 6.1 架构定位对比

| 维度 | 华为 GaussDB + HetuEngine | StarRocks | LakeSoul |
|------|-------------------------|-----------|----------|
| **本质定位** | 企业级云原生数仓 + 联邦查询 | 极速 OLAP 分析引擎 | 云原生湖仓存储框架 |
| **核心角色** | 数仓主体，向湖延伸 | 查询引擎，向湖延伸 | 存储层，向上对接引擎 |
| **自有存储** | 有（私有列存格式） | 有（内表存储） | 有（Parquet + Delta） |
| **开源属性** | 商业产品（部分开源） | Apache 2.0 开源 | Linux Foundation 开源 |
| **MPP 能力** | 强（原生 Shared-Nothing MPP） | 强（全面向量化 MPP） | 无（依赖外部引擎） |
| **存储层控制** | OBS（华为云锁定） | 任意对象存储 | 任意对象存储 |
| **元数据管理** | LakeFormation（商业服务） | 内建 + 外部 HMS | PostgreSQL（自管理） |

### 6.2 存算分离性能补偿机制对比

| 机制 | 华为 GaussDB(DWS) | StarRocks | LakeSoul |
|------|-------------------|-----------|----------|
| **本地缓存** | EVS 磁盘缓存，建议 30% 数据量 | Data Cache（内存+NVMe），支持 SLRU | NativeIO 本地热数据缓存（3.0 新增） |
| **缓存淘汰** | LRU | LRU / SLRU（分段 LRU） | 基础 LRU |
| **缓存预热** | 无显式预热机制 | CACHE SELECT 显式预热 | 无显式预热机制 |
| **计算下推** | 近数据计算（存储层执行） + HetuEngine 跨源下推 | 分区裁剪、列裁剪、谓词下推 | 分区过滤下推（50ms/百万分区） |
| **索引加速** | Min-Max + Bitmap + B-Tree + 分区裁剪 | Bloom Filter + 前缀索引 + Zone Map | 元数据索引 + 排序键 |
| **物化加速** | Hudi 自动同步到内表 + 物化视图 | External Catalog 异步物化视图 | 无内建物化，依赖外部引擎 |
| **IO 调度** | 专有 IO 调度器，充分利用 OBS 带宽 | 自适应 IO 缓存填充 | 异步 IO（Rust tokio） |
| **冷热分层** | LMT/HPN 自动分层 | partition_duration 控制缓存有效期 | 无自动分层 |
| **向量化执行** | 行列混合向量化 | C++ 全面向量化 + SIMD | Rust NativeIO 向量化读写 |

### 6.3 湖上查询加速机制对比

| 能力 | 华为 GaussDB | StarRocks | LakeSoul + 引擎 |
|------|-------------|-----------|-----------------|
| **Hudi 查询** | 外表查询 + 自动同步 | External Catalog + Data Cache | NativeIO MOR + Presto/Doris |
| **Iceberg 查询** | 外表查询 | External Catalog + 增量物化视图 | 计划支持 |
| **查询重写** | 物化视图查询重写 | 透明查询重写（3.1+） | 依赖外部引擎 |
| **联邦查询** | HetuEngine 跨源 | JDBC External Catalog | 不支持 |
| **流批一体** | 有限（通过 MRS Flink） | 不支持原生流处理 | 强（Flink Changelog 语义） |
| **CDC 入湖** | Hudi CDC + DWS 同步 | 依赖外部工具 | 原生 CDC 采集 + 自动 Schema 演变 |

### 6.4 适用场景与 Trade-off 对比

| 场景 | 最优方案 | 次优方案 | 原因 |
|------|---------|---------|------|
| **企业级复杂分析（多源关联）** | 华为 GaussDB + HetuEngine | StarRocks | 华为的联邦查询和企业级特性更完善 |
| **实时 OLAP 仪表盘** | StarRocks | 华为 GaussDB | StarRocks 向量化引擎在交互式查询上性能更优 |
| **实时数据入湖** | LakeSoul | 华为 MRS + Hudi | LakeSoul 原生 CDC + Flink 流批一体能力更强 |
| **湖上即席查询** | StarRocks | 华为 GaussDB | StarRocks Data Cache + 物化视图组合效率更高 |
| **大规模批处理** | LakeSoul + Spark | 华为 MRS | LakeSoul NativeIO 向量化 + Gluten 引擎表现突出 |
| **跨源数据共享** | 华为 LakeFormation | LakeSoul | 华为方案企业级权限管理更成熟 |
| **成本敏感场景** | LakeSoul / StarRocks | 华为 | 开源方案无云厂商绑定，成本可控 |
| **政企合规场景** | 华为 GaussDB | — | 华为在国产替代和政企市场有独特优势 |

---

## 七、行业演进趋势与研判

### 7.1 存算分离成为不可逆趋势

**市场共识**：Databricks、Snowflake、StarRocks、华为 GaussDB 等主流产品均已拥抱存算分离。驱动力包括：

- **弹性需求**：云原生时代要求秒级扩缩容
- **成本压力**：存储和计算独立计费更经济（对象存储成本为 SSD 的 1/10~1/50）
- **数据共享**：多引擎共享同一份数据避免数据搬运

**性能补偿手段的收敛**：各厂商在缓解存算分离性能损失上的手段正在趋同——本地缓存、计算下推、智能调度、物化加速。差异化将从"是否支持"转向"实现质量和智能化程度"。

### 7.2 开放表格式标准化竞争

| 格式 | 定位 | 2025-2026 趋势 |
|------|------|---------------|
| **Apache Iceberg** | 海外事实标准 | Databricks、Snowflake、AWS 均宣布支持/原生化 |
| **Apache Paimon** | 国内流式湖仓首选 | 与 Flink 深度绑定，阿里、字节等头部企业采用 |
| **Apache Hudi** | 成熟的增量处理 | 社区活跃但增速放缓，被 Iceberg 分流 |
| **CarbonData** | 华为历史资产 | 逐渐边缘化，被 Hudi/Iceberg 替代 |
| **Delta Lake** | Databricks 专属 | Databricks 策略转向 Iceberg 兼容 |

**趋势研判**：双轨格局（海外 Iceberg + 国内 Paimon）将在 2026-2027 年基本确立。CarbonData 将进一步淡出主流技术栈。

### 7.3 统一引擎与联邦查询的博弈

两种技术路线正在竞争：

**路线一：统一引擎**（StarRocks、Doris 代表）
- 用一个高性能引擎解决所有分析需求
- 优势：极致性能、低延迟
- 劣势：难以覆盖所有数据源场景

**路线二：联邦查询**（HetuEngine、Trino、Presto 代表）
- 保持各数据源独立，通过虚拟化层统一查询
- 优势：灵活性强、不搬数据
- 劣势：联邦查询的性能上限低于本地执行

**趋势研判**：两条路线正在融合。StarRocks 在增强联邦能力（JDBC Catalog），华为在增强 GaussDB 的直接分析能力（列存 3.0 + 外表查询）。最终形态可能是"强本地引擎 + 轻量联邦扩展"。

### 7.4 华为方案的演进预判

基于现有技术路线和行业趋势，预判华为湖仓一体方案将在以下方向深化：

1. **CarbonData 渐进式退场**：未来 2-3 年内 CarbonData 可能从 MRS 核心组件降级为可选历史兼容组件，Hudi 和 Iceberg 将全面接管
2. **GaussDB 云原生深化**：VW 弹性能力继续增强，可能引入 Serverless 模式，进一步降低用户运维成本
3. **HetuEngine 与 GaussDB 的能力融合**：两者的查询优化器可能逐步统一，减少组件碎片化
4. **AI 原生能力注入**：GaussDB 可能引入基于学习的缓存预测、查询计划优化等 AI 能力
5. **Iceberg/Paimon 的原生支持**：GaussDB 对 Iceberg 和 Paimon 的支持将从"可查询"升级到"深度集成"（如增量同步、物化视图、查询重写）

---

## 八、限定场景再评估：SmartCare 网络观测数据下的 CarbonData

> **场景限定条件**：华为 SmartCare 产品；网络域观测数据（KPI/MR/话单/信令等）；数据只读（Append-only，不更新）；分析模式以多维 OLAP 聚合和时空查询为主。

### 8.1 场景特征分析：网络观测数据的独特性

网络域观测数据与通用企业数据有本质区别，这些特征对存储格式的选择产生决定性影响：

| 特征 | 网络观测数据 | 通用企业数据 |
|------|-------------|-------------|
| **写入模式** | Append-only，只追加不更新 | 频繁 Upsert/Delete |
| **数据规模** | 极大（每日 14TB+/2000万用户网络，百亿级记录） | 中等到大 |
| **更新需求** | 无——写入即不可变 | 高频更新 |
| **查询模式** | 多维聚合（时间×区域×小区×KPI）+ 时空范围查询 | 多样化 |
| **维度特征** | 高基数（用户号码）+ 低基数（区域/小区/KPI类型）混合 | 视业务而定 |
| **时间属性** | 强时序性，自然按小时/天/月分层 | 弱时序性 |
| **空间属性** | 强空间性（经纬度、网格、行政区、小区覆盖区） | 通常无空间属性 |
| **并发特征** | 中低并发（5-20分析师）的复杂查询 | 高并发简单查询 |
| **生命周期** | 按时间自然老化（热→温→冷→归档） | 不规律 |

**关键洞察**：这个场景恰好**绕开了 CarbonData 的所有短板**（无 Upsert/事务管理需求、无 Schema 频繁演进需求），同时**命中了 CarbonData 的全部长板**（多维索引、时空索引、预聚合、列存压缩、只读 OLAP 优化）。

### 8.2 CarbonData 在该限定场景下的优势重估

在通用湖仓一体评估中，CarbonData 因缺乏现代湖仓能力（事务、CDC、Schema 演进、Time Travel）而被判为"角色弱化"。但在 SmartCare 网络观测数据的限定场景下，这个结论需要**显著修正**：

#### 优势一：多级索引体系——为网络 KPI 多维查询量身定制

CarbonData 的核心架构是"列存 + 伴随索引"，其索引体系深度远超 Parquet/ORC：

```
CarbonData 索引层级：

File Level
  └── Block Level 索引（B+树，Block 级别元数据）
        └── Blocklet Level 索引（≤64MB，细粒度 min-max）
              └── Page Level 索引
                    └── Column Chunk 级索引

相比之下：
  Parquet：仅 Row Group 级 min-max 统计 + 可选 Bloom Filter
  ORC：仅 Stripe 级统计 + 可选 Bloom Filter
```

对于网络 KPI 查询（如"查询上海浦东区域 2024年1月 所有 4G 小区的平均下行吞吐率"），CarbonData 可以在多个层级快速裁剪数据，实际读取量可降低 1-2 个数量级。

#### 优势二：全局字典编码——高压缩率 + 编码上直接计算

网络数据中大量低基数维度列（运营商编码、设备类型、KPI 类型、制式等），CarbonData 的全局字典编码可以：
- 将字符串列压缩为整型编码，**压缩率 60-80%**
- GROUP BY 和聚合操作直接在编码数据上执行，**避免字符串比较开销**
- 仅在最终返回结果时才解码（延迟物化）

#### 优势三：Sort Columns 优化——适配网络查询 pattern

CarbonData 允许指定 Sort Columns，数据按此排序存储。对于网络数据，典型的 sort 配置为：

```sql
TBLPROPERTIES ('SORT_COLUMNS'='time_stamp, region_id, cell_id')
```

这使得"按时间+区域+小区"的多维查询天然获得数据局部性，极大提升了过滤效率。

#### 优势四：二级索引——精确加速高基数列查询

对于用户号码（MSISDN）等高基数列，CarbonData 支持创建二级索引：

```sql
CREATE INDEX idx_msisdn ON TABLE network_kpi (msisdn) AS 'carbondata'
```

这使得"查询指定用户的网络质量历史"这类点查也能高效完成，而 Parquet/ORC 在此场景需要全量扫描。

### 8.3 CarbonData 时空索引：电信网络的"杀手级特性"

这是 CarbonData 在网络观测领域的**独占优势**——Hudi、Iceberg、Parquet、ORC 截至 2026 年初均不具备生产可用的时空索引能力。

#### 时空索引原理

网络覆盖分析需要将地表按 50×50 米网格切分，按"时间+空间"二维进行查询。传统方案的痛点是：经纬度按数值排序后，空间相邻的网格在存储上被切割为不相邻的条带，导致大量随机 IO。

CarbonData 通过 GeoHash/GeoSOT 空间填充曲线解决此问题：

```
传统排序：按 (latitude, longitude) 排序
  → 空间相邻数据在存储上不相邻
  → 区域查询需大量随机IO

CarbonData 空间索引：按 GeoID (空间填充曲线编码) 排序
  → 空间相邻数据在存储上也相邻
  → 区域查询变为顺序IO
```

#### 空间查询语法

```sql
-- 查询多边形区域内的网络覆盖数据
SELECT cell_id, avg(rsrp), avg(sinr) 
FROM network_mr_data
WHERE IN_POLYGON('116.321 39.123, 116.337 39.947, 116.560 39.935')
  AND dt = '2024-01-15'
GROUP BY cell_id;
```

#### 实际性能数据

华为实测结果：从 2000 亿行到 1 万亿行数据，数据量增长 5x 而查询时间增长不到 1x，体现了**近似线性扩展**的时空查询能力。

#### 竞品对比

| 特性 | CarbonData | Iceberg | Hudi | Parquet/ORC |
|------|-----------|---------|------|-------------|
| 空间索引（生产就绪） | ✅ GeoHash + GeoSOT | ❌ WIP（开发中） | ❌ 不支持 | ❌ 不支持 |
| IN_POLYGON 查询 | ✅ 原生支持 | ❌ | ❌ | ❌ |
| 空间填充曲线排序 | ✅ 内建 | 🔶 Hilbert 排序（开发中） | ❌ | ❌ |
| 多维组合索引 | ✅ Sort + Spatial + Secondary | 🔶 Z-order/Hilbert（分区级） | 🔶 Z-order（有限） | ❌ |

**Iceberg 的地理空间支持（GEOMETRY/GEOGRAPHY 类型 + XZ2 分区变换）截至 2026 年初仍处于 WIP 状态**，依赖于尚未发布的 Parquet Java 新版本。这意味着在可预见的 1-2 年内，CarbonData 在电信时空分析场景中仍具有独占优势。

### 8.4 预聚合与时间序列 DataMap：内建 KPI 汇聚能力

网络观测数据的一个核心分析模式是多时间粒度的 KPI 汇聚。CarbonData 内建了 Timeseries DataMap，无需外部 ETL 工具即可完成：

```sql
-- 创建小时级预聚合
CREATE DATAMAP agg_hour ON TABLE network_kpi
USING "timeseries"
DMPROPERTIES ('event_time'='collect_time', 'hour_granularity'='1')
AS SELECT collect_time, region_id, cell_id,
          sum(dl_traffic), avg(dl_throughput), max(user_count)
   FROM network_kpi
   GROUP BY collect_time, region_id, cell_id;

-- 创建天级预聚合
CREATE DATAMAP agg_day ON TABLE network_kpi
USING "timeseries"
DMPROPERTIES ('event_time'='collect_time', 'day_granularity'='1')
AS SELECT collect_time, region_id,
          sum(dl_traffic), avg(dl_throughput)
   FROM network_kpi
   GROUP BY collect_time, region_id;
```

**自动路由**：查询时 CarbonData 自动匹配最优预聚合表，无需修改查询 SQL。例如查询"过去 7 天各区域日均下行流量"时，自动路由到 `agg_day` 而非扫描原始明细数据。

**对比**：这种内建预聚合在 Hudi/Iceberg 中不存在，需要依赖外部工具（如 StarRocks 物化视图、Spark 定时任务）来实现，增加了架构复杂度。

### 8.5 限定场景下与 Hudi/Iceberg/Parquet 的对比逆转

在 SmartCare 网络观测数据的限定场景下，存储格式的优劣排序与通用场景**完全逆转**：

| 能力维度 | CarbonData | Hudi | Iceberg | 裸 Parquet |
|---------|-----------|------|---------|-----------|
| **多维 OLAP 查询（核心需求）** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **时空范围查询（核心需求）** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐（开发中） | ⭐ |
| **KPI 时序预聚合（核心需求）** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ |
| **压缩率（成本控制）** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **只读扫描性能** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Upsert/CDC（**不需要**） | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| Schema 演进（**弱需求**） | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Time Travel（**弱需求**） | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| 社区生态活跃度 | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**结论**：在"只读 + 多维分析 + 时空查询"三个核心需求维度上，CarbonData 都是最优选择。Hudi/Iceberg 的核心优势（事务、CDC、Schema 演进）在此场景下完全是"过度设计"，反而引入了不必要的写放大和元数据开销。

### 8.6 修正后的结论

对于原报告中"CarbonData 角色弱化"的判断，在 SmartCare 网络观测数据场景下需做如下修正：

#### 通用场景 vs SmartCare 场景的判断对比

| 判断维度 | 通用湖仓场景（原结论） | SmartCare 网络观测场景（修正结论） |
|---------|---------------------|-------------------------------|
| CarbonData 竞争力 | 弱化，被 Hudi/Iceberg 替代 | **强势**，在核心需求上无可替代 |
| 关键差异化能力 | 无明显差异化 | **时空索引 + 预聚合 + 多维索引**三重独占优势 |
| 替代方案成熟度 | Hudi/Iceberg 成熟可用 | Iceberg 地理空间仍在开发中，**1-2年内无替代** |
| 生态风险 | 社区活跃度下降 | 华为内部持续维护（SmartCare/MRS 为核心营收产品），**短期无风险** |
| 建议策略 | 制定迁移路线图 | **继续使用 CarbonData**，但关注 Iceberg 地理空间功能进展 |

#### 需要关注的长期风险

尽管在当前场景下 CarbonData 仍是最优选择，但以下长期风险不应忽视：

1. **社区维度**：Apache CarbonData 的社区贡献者主要来自华为，外部贡献极少。一旦华为内部战略调整，项目可能缺乏持续演进动力
2. **生态兼容性**：随着 Iceberg 在全行业的标准化，越来越多的工具和引擎（Spark、Flink、Trino、StarRocks）都在优化 Iceberg 路径。CarbonData 的引擎集成广度有限（主要限于 Spark 和 Presto）
3. **Iceberg 追赶**：Iceberg 的 Geospatial 支持一旦 GA，将迅速缩小与 CarbonData 的差距。Iceberg 的 Hilbert 排序 + XZ2 分区变换在理论能力上与 GeoHash/GeoSOT 等价
4. **查询引擎耦合**：CarbonData 深度绑定 Spark 生态，而 SmartCare 未来如果需要引入更高性能的 MPP 引擎（如 StarRocks/Doris），CarbonData 的集成支持可能成为瓶颈

#### 推荐策略

**当前（2026-2027）**：在 SmartCare 场景中继续使用 CarbonData，充分利用其时空索引和预聚合能力。

**中期（2027-2028）**：关注 Iceberg Geospatial GA 进展。一旦 Iceberg 地理空间功能达到生产就绪，评估迁移的可行性和收益。

**长期准备**：设计数据层的抽象接口，使上层应用不直接耦合 CarbonData API，为未来可能的格式迁移预留灵活性。

---

## 九、给技术决策者的建议

### 场景化选型指南

| 如果你是... | 推荐方案 | 关键理由 |
|------------|---------|---------|
| 华为云存量客户，需要湖仓一体 | GaussDB(DWS) 3.0 + HetuEngine + LakeFormation | 生态一致性，统一运维，政企合规优势 |
| 追求极致 OLAP 性能 + 湖上分析 | StarRocks（存算一体 + External Catalog） | 向量化 MPP 性能无对手，Data Cache 机制成熟 |
| 实时数据入湖 + 流批一体 | LakeSoul + Flink + Presto/Doris | 原生 CDC、NativeIO 性能优秀、无厂商锁定 |
| 多云/混合云，需要避免锁定 | LakeSoul / StarRocks | 开源社区驱动，多云中立 |
| 弹性优先、成本敏感 | StarRocks（存算分离） / GaussDB（存算分离） | 秒级扩缩容 + 对象存储低成本 |

### 关于华为方案的注意事项

1. **评估 CarbonData 的退出影响**：如果当前重度依赖 CarbonData，建议制定向 Hudi/Iceberg 迁移的路线图
2. **合理配置 EVS 缓存**：缓存容量直接影响性能体验，建议初期按 30% 数据量配置，后续根据监控调整
3. **选择合适的查询路径**：不要一刀切地使用外表直查，热数据应通过物化同步到内表
4. **评估 HetuEngine 的引入时机**：如果仅使用 GaussDB + OBS，HetuEngine 不是必须的；当需要跨源分析时再引入

---

## 附录：参考来源索引

### A. 华为官方技术文档

| 编号 | 来源 | 地址 |
|------|------|------|
| [H1] | GaussDB(DWS) 湖仓融合技术解析 | https://bbs.huaweicloud.com/blogs/425556 |
| [H2] | GaussDB(DWS) 湖仓融合：Hudi与元数据打通深度解析 | https://juejin.cn/post/7352661916386377766 |
| [H3] | 体验 GaussDB(DWS) 云原生数仓-存算分离 | https://bbs.huaweicloud.com/blogs/415625 |
| [H4] | DWS 3.0 存算分离使用建议及性能优化 | https://support.huaweicloud.com/bestpractice-dws/dws_05_0027.html |
| [H5] | GaussDB(DWS) 产品架构 | https://www.huaweicloud.com/product/dws/architecture.html |
| [H6] | GaussDB(DWS) 核心技术 | https://www.huaweicloud.com/product/dws/key-technology.html |
| [H7] | HetuEngine 交互查询引擎概述 | https://support.huaweicloud.com/cmpntguide-lts-mrs/mrs_01_2315.html |
| [H8] | HetuEngine 数据源对接 | https://bbs.huaweicloud.com/blogs/407284 |
| [H9] | HetuEngine CTE 缓存配置 | https://support.huaweicloud.com/intl/zh-cn/eu-west-0-cmpntguide-lts-mrs/mrs_01_24181.html |
| [H10] | HetuEngine 元数据缓存 | https://support.huaweicloud.com/cmpntguide-lts-mrs/mrs_01_1746.html |
| [H11] | LakeFormation 产品介绍 | https://support.huaweicloud.com/intl/zh-cn/productdesc-lakeformation/lakeformation_01_0001.html |
| [H12] | LakeFormation 多服务/多集群共享元数据 | https://support.huaweicloud.com/intl/zh-cn/productdesc-lakeformation/lakeformation_01_0005.html |
| [H13] | Querying Data on OBS Through Foreign Tables | https://support.huaweicloud.com/intl/en-us/migration-dws/dws_15_0017.html |
| [H14] | CarbonData 组件介绍 | https://support.huaweicloud.com/intl/zh-cn/ae-ad-1-usermanual-mrs/mrs_08_0015.html |
| [H15] | CarbonData Spark2x 增强特性 | https://support.huaweicloud.com/intl/zh-cn/ae-ad-1-usermanual-mrs/mrs_08_007108.html |
| [H16] | CarbonData 二级索引 | https://support.huaweicloud.com/intl/zh-cn/ae-ad-1-cmpntguide-mrs/mrs_01_1445.html |
| [H17] | 华为云 Stack 智能数据湖湖仓一体方案 | https://www.huaweicloud.com/zhishi/huaweicloudstack07.html |
| [H18] | GaussDB(DWS) 物化视图概述 | https://support.huaweicloud.com/devg-dws/dws_04_1414.html |
| [H19] | GaussDB(DWS) 冷热数据管理 | https://bbs.huaweicloud.com/blogs/282033 |
| [H20] | GaussDB(DWS) Hudi 外表创建 | https://support.huaweicloud.com/devg-dws/dws_04_1073.html |
| [H21] | GaussDB(DWS) Hudi 同步任务 | https://support.huaweicloud.com/devg-dws/dws_04_1074.html |
| [H22] | GaussDB(DWS) 分布式计划详解 | https://bbs.huaweicloud.com/blogs/200449 |
| [H23] | GaussDB(DWS) 云原生数仓技术解析 | https://www.cnblogs.com/huaweiyun/p/17292964.html |
| [H24] | GaussDB(DWS) 云原生数仓直播回顾 | https://bbs.huaweicloud.com/blogs/396028 |
| [H25] | GaussDB(DWS) 全场景数仓 | https://www.modb.pro/db/1807983867222134784 |
| [H26] | OBS 存算分离方案概述 | https://support.huaweicloud.com/intl/en-us/bestpractice-obs/obs_05_1501.html |
| [H27] | 添加 GAUSSDB 数据源 | https://support.huaweicloud.com/cmpntguide-lts-mrs/mrs_01_2351.html |
| [H28] | 数仓集群通信技术详解 | https://bbs.huaweicloud.com/blogs/420534 |

### B. StarRocks 技术文档

| 编号 | 来源 | 地址 |
|------|------|------|
| [S1] | StarRocks Data Cache 官方文档 | https://docs.starrocks.io/zh/docs/3.5/data_source/data_cache/ |
| [S2] | StarRocks 3.0 Lakehouse 架构 | https://tech.chinadaily.com.cn/a/202406/24/WS667929a7a3107cd55d268488.html |
| [S3] | Data Cache 阿里云 EMR 集成 | https://help.aliyun.com/zh/emr/emr-serverless-starrocks/data-lake-data-cache |
| [S4] | StarRocks 数据湖分析能力边界 | https://docs.starrocks.io/zh/docs/3.5/data_source/feature-support-data-lake-analytics/ |
| [S5] | StarRocks Data Lakehouse 官方文档 | https://docs.starrocks.io/docs/data_source/data_lakes |
| [S6] | 存算分离与存算一体功能差异 | https://docs.starrocks.io/zh/docs/3.5/introduction/feature_difference/ |
| [S7] | 存算分离集群能力边界 | https://docs.starrocks.io/zh/docs/deployment/feature-support-shared-data/ |
| [S8] | StarRocks 深入解析（火山引擎） | https://developer.volcengine.com/articles/7624745772680937510 |
| [S9] | Data Lake Query Acceleration with Materialized Views | https://docs.starrocks.io/docs/using_starrocks/async_mv/use_cases/data_lake_query_acceleration_with_materialized_views/ |
| [S10] | Unified Catalog | https://docs.starrocks.io/docs/data_source/catalog/unified_catalog |
| [S11] | 阿里云 EMR StarRocks 物化视图加速数据湖查询 | https://www.alibabacloud.com/help/en/emr/emr-serverless-starrocks/use-materialized-views-to-accelerate-data-lake-queries |
| [S12] | 白山云 StarRocks 湖仓一体实践 | https://www.infoq.cn/article/1eqikwuyfnttr1p4ewkw |
| [S13] | StarRocks 支持 Apache Hudi 原理解析 | https://mp.weixin.qq.com/s/oROdpb4dHjGwTM8xLvKsWw |
| [S14] | Data Cache 预热 | https://docs-server.mirrorship.cn/zh/docs/3.5/data_source/data_cache_warmup/ |
| [S15] | 缓存感知 Scan Range 均衡（PR #51996） | https://github.com/StarRocks/starrocks/pull/51996 |
| [S16] | 自适应缓存填充（PR #48783） | https://github.com/StarRocks/starrocks/pull/48783 |
| [S17] | 增量 Scan Range 部署（Issue #50196） | https://github.com/StarRocks/starrocks/issues/50196 |
| [S18] | 阿里云 EMR StarRocks 本地缓存 | https://help.aliyun.com/zh/emr/emr-serverless-starrocks/use-cases/use-local-caching-to-improve-query-performance-in-compute-storage-separation-mode-in-emr-serverless-starrocks-3-1 |
| [S19] | 存算分离 Data Cache 文档 | https://help.aliyun.com/zh/emr/emr-serverless-starrocks/storage-compute-separation-data-cache |

### C. LakeSoul 技术文档

| 编号 | 来源 | 地址 |
|------|------|------|
| [L1] | LakeSoul 介绍 | https://lakesoul-io.github.io/zh-Hans/docs/intro |
| [L2] | LakeSoul 总体概念介绍 | https://lakesoul-io.github.io/zh-Hans/docs/Getting%20Started/concepts |
| [L3] | LakeSoul 3.0.0 发布说明 | https://lakesoul-io.github.io/blog/2025/09/05/lakesoul-3.0.0-release |
| [L4] | LakeSoul NativeIO 实现原理 | https://lakesoul-io.github.io/zh-Hans/blog/2024/01/10/lakesoul-native-io |
| [L5] | LakeSoul 博客汇总 | https://lakesoul-io.github.io/zh-Hans/blog |
| [L6] | LakeSoul 简介（数元灵科技） | https://www.dmetasoul.com/docs/lakesoul/ |
| [L7] | 使用 Presto 查询 LakeSoul 表 | https://lakesoul-io.github.io/zh-Hans/docs/Usage%20Docs/setup-presto |
| [L8] | 使用 Doris 和 LakeSoul | https://doris.apache.org/zh-CN/docs/3.x/lakehouse/best-practices/doris-lakesoul/ |

### D. CarbonData 电信/时空分析专题

| 编号 | 来源 | 地址 |
|------|------|------|
| [C1] | 基于CarbonData的电信时空大数据探索（InfoQ） | https://xie.infoq.cn/article/7f6c4cb8f1b2193a10e16a353 |
| [C2] | CarbonData 空间索引文档（MRS 官方） | https://support.huaweicloud.com/intl/zh-cn/ae-ad-1-cmpntguide-mrs/mrs_01_1451.html |
| [C3] | CarbonData 空间索引指南（Apache 官方） | https://carbondata.apache.org/spatial-index-guide.html |
| [C4] | CarbonData 预聚合 DataMap 指南 | https://carbondata.apache.org/preaggregate-datamap-guide.html |
| [C5] | CarbonData 时间序列 DataMap 指南 | https://carbondata.apache.org/timeseries-datamap-guide.html |
| [C6] | CarbonData+Spark SQL 应用实践与调优（InfoQ） | https://www.infoq.cn/article/2017/09/carbondata-spark-huawei |
| [C7] | 单表千亿电信大数据场景：Spark+CarbonData 替换 Impala 案例 | https://www.ancii.com/aywq5zgve/ |
| [C8] | Apache CarbonData 2.0 预览（华为云社区） | https://bbs.huaweicloud.cn/blogs/163408 |
| [C9] | CarbonData 性能分析（亿速云） | http://www.yisu.com/jc/276576.html |
| [C10] | CarbonData 深度解析（博客园） | https://www.cnblogs.com/happenlee/p/9202236.html |
| [C11] | CarbonData 初探（Hexiaoqiao） | http://hexiaoqiao.github.io/blog/2016/10/01/carbondata-column-based-storage-format/ |
| [C12] | Apache Iceberg Geospatial 支持（Issue #10260） | https://github.com/apache/iceberg/issues/10260 |
| [C13] | Parquet GEOMETRY/GEOGRAPHY 类型（PR #240） | https://github.com/apache/parquet-format/pull/240 |
| [C14] | 华为 SmartCare 解决方案（C114） | https://m.c114.com.cn/w126-644729.html |
| [C15] | FusionInsight 大数据平台（华为出版物） | https://www.huawei.com/en/huaweitech/publication/77/big-results-from-big-data |
| [C16] | CarbonData 成为 Apache 顶级项目（华为新闻） | https://www.huawei.com/en/news/2017/4/Huawei-CarbonData-Program |

### E. 行业分析与趋势

| 编号 | 来源 | 地址 |
|------|------|------|
| [I1] | 2025 Lakehouse 趋势全景展望 | https://news.qq.com/rain/a/20250310A04YMG00 |
| [I2] | 2025 湖仓趋势展望：开放架构与实时分析融合演进 | https://tech.ifeng.com/c/8htp5jbnH0A |
| [I3] | Snowflake vs Databricks 2026 对比 | https://tech-insider.org/snowflake-vs-databricks-2026-2/ |
| [I4] | Snowflake 和 Databricks 湖仓一体趋势分析 | https://www.esensoft.com/industry-news/dx-5721.html |
| [I5] | 云器 Lakehouse 超越 Spark 10倍性能解析 | https://yunqi.tech/resource/blogs/technical-lakehouse-spark-10 |
| [I6] | Adaptive and Robust Query Execution for Lakehouses（VLDB） | https://www.vldb.org/pvldb/vol18/p4831-ritter.pdf |
| [I7] | Building the Next-Generation Data Lakehouse (Apache Doris) | https://doris.apache.org/zh-CN/blog/Building-the-Next-Generation-Data-Lakehouse-10X-Performance/ |
| [I8] | 字节跳动基于 Apache Hudi 的湖仓一体方案 | https://developer.volcengine.com/articles/7317470910794268698 |
| [I9] | Lakehouse Federation Performance (Databricks) | https://docs.databricks.com/aws/en/query-federation/performance-recommendations |
| [I10] | 腾讯云 Adaptive Query Execution 解析 | https://cloud.tencent.com.cn/developer/article/2487694 |

---

*本报告基于公开可获取的技术文档、官方博客、社区讨论和行业分析编写。华为产品的部分内部实现细节可能与文档描述存在差异，建议通过 PoC 验证关键性能指标。*
