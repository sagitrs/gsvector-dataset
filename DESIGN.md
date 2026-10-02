# gsvector-dataset 多格式数据集设计

**日期：** 2026-06-24
**类型：** 架构设计
**状态：** Draft

## 问题

gsvector-dataset 当前仅提供 `.fvecs` 与 `.ivecs` 两种向量格式。各消费者仓库需要的格式并不相同，下表逐仓列出其测试类型、所需格式，以及当前是否已具备。

| 仓库 | 测试类型 | 需要格式 | 当前状态 |
|------|---------|---------|:--:|
| gsvector (C++) | benchmark, recall | `.fvecs` + `.ivecs` | ✅ |
| gsvector (Python) | binding test, perf | numpy array (加载 `.fvecs`) | ✅ |
| gsvector-pg | SQL regression | `.csv` (PG COPY) | ❌ |
| gsiceberg | FDW integration | Iceberg table (Parquet + metadata) | ❌ |

## 方案：从 fvecs 单向转换

本方案不重造源数据，而是从已就绪的 `.fvecs` 文件生成目标格式。这样源数据只有一份，两种派生格式都可以随时重新生成。

```
.fvecs (source, LFS-tracked)
  ├── fvecs2csv.py       → .csv        (gsvector-pg)
  └── fvecs2iceberg.py   → Parquet +   (gsiceberg)
                            metadata.json
```

## 目录结构（以 sift/1k 为例）

每个数据集目录同时容纳源文件与两种派生格式。下图标出各文件是既有还是新增。

```
sift/1k/
  base.fvecs          ← 现有（LFS）
  query.fvecs         ← 现有（LFS）
  gt_top10.ivecs      ← 现有（LFS）
  gt_top100.ivecs     ← 现有（LFS）
  base.csv            ← 新增
  query.csv           ← 新增
  iceberg/            ← 新增
    data/
      base.parquet
      query.parquet
    metadata/
      metadata.json
      snap-*.avro
```

## 子文档

两种派生格式各有一份子设计文档，Makefile 的扩展另有一份：

| 文档 | 内容 |
|------|------|
| [docs/csv-format.md](docs/csv-format.md) | CSV 格式生成器 |
| [docs/iceberg-format.md](docs/iceberg-format.md) | Iceberg 格式生成器 |
| [docs/makefile-targets.md](docs/makefile-targets.md) | Makefile 扩展 (`make csv`, `make iceberg`) |

## 规模

下表给出 100k 规模以内各数据集的大小估算，用于判断哪些规模适合放进大文件存储（Large File Storage，下称 LFS）。

| 数据集 | 1k | 10k | 100k |
|--------|----|-----|------|
| SIFT (128-dim) | ~0.5 MB | ~5 MB | ~50 MB |
| GIST (960-dim) | ~4 MB | ~38 MB | ~380 MB |

CSV 与 Iceberg 带来的增量约为原始大小的两倍。100k 规模仍在 LFS 可接受的范围内。

## 构建性能

格式转换与输入输出（Input/Output，下称 IO）紧密相关，属 IO 密集型任务。多个数据集可以用 `make -jN csv` 或 `make -jN iceberg` 并行构建：模式规则之间没有依赖，GNU Make 会自动并行调度。
