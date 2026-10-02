# Iceberg 格式生成器

**日期：** 2026-06-24
**类型：** 子设计文档
**依赖：** [主文档](../DESIGN.md)

## 目标

本档说明如何为 gsiceberg 的外部数据包装器（Foreign Data Wrapper，下称 FDW）集成测试生成 Iceberg table 格式的数据集。

## Iceberg table 结构

一个数据集目录下的 Iceberg 表由两部分组成：`data/` 存放 Parquet 向量数据，`metadata/` 存放表元数据与快照。下图标出各文件的作用。

```
iceberg/
  data/
    base.parquet        ← 向量数据
    query.parquet       ← 查询向量
  metadata/
    metadata.json       ← table metadata + snapshot refs
    snap-*.avro         ← manifest list (Apache Avro)
```

### metadata.json（最小可挂载）

要挂载一张表，`metadata.json` 至少需要下列字段。这个例子取自一张 128 维、单快照的表。

```json
{
  "format-version": 1,
  "table-uuid": "fb6c3100-...",
  "location": "/warehouse/test_sift_1k",
  "last-updated-ms": 1719000000000,
  "current-schema-id": 0,
  "schemas": [
    {"schema-id": 0, "type": "struct",
     "fields": [
       {"id": 1, "name": "id", "type": "long", "required": true},
       {"id": 2, "name": "v0", "type": "float", "required": true},
       ...
       {"id": 129, "name": "v127", "type": "float", "required": true}
     ]}
  ],
  "snapshots": [
    {"snapshot-id": 1, "parent-snapshot-id": null,
     "timestamp-ms": 1719000000000,
     "manifest-list": "metadata/snap-1.avro",
     "summary": {"operation": "append"}}
  ]
}
```

## 转换脚本：`scripts/fvecs2iceberg.py`

脚本接收一个 base 文件、一个 query 文件与一个输出目录，产出下列四个文件。

```
fvecs2iceberg.py <base.fvecs> <query.fvecs> <output_dir/>

生成:
  output_dir/iceberg/data/base.parquet
  output_dir/iceberg/data/query.parquet
  output_dir/iceberg/metadata/metadata.json
  output_dir/iceberg/metadata/snap-1.avro
```

### 依赖

写出 Parquet 文件需要 `pyarrow`，写出 manifest 需要 `fastavro` 或 `avro`。

### 实现要点

实现分五步。第一步读取 fvecs 文件，得到 numpy 数组。第二步构建 PyArrow Table，其中 `id` 列为 int64，`v0` 到 `v{d-1}` 列为 float32。第三步把该表写入 Parquet 文件。第四步生成 `metadata.json`，其 schema 由维度 `dim` 推导。第五步生成只含一个条目的 manifest list，格式为 Avro。

## Makefile 集成

```makefile
sift/1k/iceberg/metadata/metadata.json: sift/1k/base.fvecs scripts/fvecs2iceberg.py
        $(PYTHON) scripts/fvecs2iceberg.py $< sift/1k/query.fvecs sift/1k/

iceberg: $(foreach ds,$(ALL_DATASETS),$(foreach sz,$(NON_1M_SIZES),$(ds)/$(sz)/iceberg/metadata/metadata.json))
```
