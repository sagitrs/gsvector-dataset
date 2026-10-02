# Makefile 目标扩展

**日期：** 2026-06-24
**类型：** 子设计文档
**依赖：** [主文档](../DESIGN.md), [CSV](csv-format.md), [Iceberg](iceberg-format.md)

## 新增 Makefile 目标

本档在既有目标之外新增三个目标，分别生成 CSV 格式、Iceberg 格式，或一次生成全部格式。

```makefile
# 现有目标（不变）
make sift              # fvecs + ivecs + ground truth
make ci                # 1k fvecs only
make bench             # up to BENCH_MAX_SIZE

# 新增
make csv               # 为所有数据集生成 CSV 格式
make iceberg           # 为所有数据集生成 Iceberg 格式
make all-formats       # make all + csv + iceberg (全量)
```

## 目标依赖链

`make csv` 与 `make iceberg` 各自的目标都依赖同一个 `base.fvecs` 源文件。下面的图给出两种格式的依赖关系。

```
make csv:
  sift/1k/base.csv      ← sift/1k/base.fvecs → scripts/fvecs2csv.py
  sift/10k/base.csv     ← sift/10k/base.fvecs
  ...
  gist/1k/base.csv      ← gist/1k/base.fvecs
  ...

make iceberg:
  sift/1k/iceberg/metadata/metadata.json  ← sift/1k/base.fvecs → scripts/fvecs2iceberg.py
  ...
```

## 模式规则

转换由两条模式规则驱动，它们分别覆盖 CSV 与 Iceberg 两种输出。

```makefile
# CSV: fvecs → CSV
%/base.csv: %/base.fvecs scripts/fvecs2csv.py
	$(PYTHON) scripts/fvecs2csv.py $< $@

%/query.csv: %/query.fvecs scripts/fvecs2csv.py
	$(PYTHON) scripts/fvecs2csv.py $< $@

# Iceberg: fvecs → Parquet + metadata
%/iceberg/metadata/metadata.json: %/base.fvecs scripts/fvecs2iceberg.py
	@echo "=== all-formats: DONE ==="
```

## 并行构建

数据集构建与输入输出（Input/Output，下称 IO）紧密相关，属 IO 密集型任务，主要开销在读写 fvecs 与 Parquet 文件。因此可以用 Make 的 `-j` 标志并行构建多个数据集。

```bash
make -j4 csv       # 4 个数据集并行转换
make -j8 iceberg   # 8 个 Iceberg 表并行构建
```

Makefile 中无需特殊配置，因为模式规则天然支持并行。每个 `%/base.csv` 目标互不依赖，GNU Make 会自动调度它们。

## 与现有 CI 集成

消费者仓库的 CI 可以按需调用这两个目标来准备数据。

```makefile
# gsvector-pg CI 准备数据
make csv DATASET=sift SIZE=1k

# gsiceberg CI 准备数据  
make iceberg DATASET=sift SIZE=1k
```

消费者仓库先通过 `make fetch-datasets-ci` 获取 fvecs 数据，再按需运行 `make csv` 或 `make iceberg`。
